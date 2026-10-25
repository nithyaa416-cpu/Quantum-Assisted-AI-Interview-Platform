"""
QAOA (Quantum Approximate Optimization Algorithm) Knapsack & QUBO Optimizer.

Formulates candidate interview preparation planning as a constrained 0-1 Knapsack problem with
prerequisite dependencies, mapped to a Quadratic Unconstrained Binary Optimization (QUBO) model,
and solved via QAOA on a local Qiskit statevector quantum circuit.

Includes:
1. Multi-objective activity value calculation:
   v_i = 100 * (0.40 * gap_i + 0.35 * relevance_i + 0.25 * impact_i) * (1.15 if priority else 1.0)
2. Capacity & Prerequisite QUBO mapping with penalty terms
3. Mapping to Ising spin Hamiltonian: x_i = (1 - Z_i) / 2
4. Parameterized QAOA quantum circuit (p=1 or p=2) with cost and mixer unitaries
5. Classical optimization loop (COBYLA) via Qiskit Statevector simulation
6. Statevector probability measurement and ranking
7. Deterministic repair algorithm enforcing prerequisite feasibility and budget capacity
8. Exact Classical Branch-and-Bound / DP benchmark solver for comparative validation
9. Resilient classical fallback when quantum execution is unavailable or exceeds constraints
"""

import time
import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy.optimize import minimize

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

logger = logging.getLogger(__name__)

# Maximum problem size for local fast QAOA statevector simulation
MAX_QAOA_QUBITS = 10


def calculate_activity_value(
    activity: Dict[str, Any],
    priority_areas: Optional[List[str]] = None
) -> float:
    """
    Computes normalized multi-objective preparation value v_i in range [1.0, 100.0].
    
    Weights:
    - 40% Skill gap severity (addressing verified interview weaknesses)
    - 35% Role relevance (alignment with target job profile)
    - 25% Selection impact estimate (expected leverage in hiring rounds)
    + 15% User priority boost if topic/category matches user-declared priority areas.
    """
    gap = float(activity.get('skill_gap_severity', 0.5))
    relevance = float(activity.get('role_relevance', 0.5))
    impact = float(activity.get('selection_impact_estimate', 0.5))
    
    # Base weighted value (0.0 to 100.0)
    base_val = 100.0 * (0.40 * gap + 0.35 * relevance + 0.25 * impact)
    
    # Priority area multiplier
    multiplier = 1.0
    if priority_areas:
        priority_lower = [p.lower().strip() for p in priority_areas]
        topic_id = str(activity.get('id', '')).lower()
        topic_name = str(activity.get('topic', '')).lower()
        category = str(activity.get('category', '')).lower()
        
        matches = any(
            p in topic_id or p in topic_name or p in category or topic_id in p
            for p in priority_lower
        )
        if matches:
            multiplier = 1.15
            
    final_val = base_val * multiplier
    return max(1.0, min(100.0, round(final_val, 2)))


def build_qubo_matrix(
    values: List[float],
    weights: List[float],
    capacity: float,
    prereq_pairs: List[Tuple[int, int]],
    budget_penalty_weight: Optional[float] = None,
    prereq_penalty_weight: Optional[float] = None
) -> Tuple[np.ndarray, float]:
    """
    Constructs upper-triangular QUBO matrix Q such that cost(x) = x^T Q x + const.
    
    Minimize:
      - sum_i v_i x_i
      + P_budget * (sum_i w_i x_i - W)^2
      + P_prereq * sum_{(j, i)} x_i (1 - x_j)
      
    where:
      (sum w_i x_i - W)^2 = sum_i (w_i^2 - 2 W w_i) x_i + 2 sum_{i < k} w_i w_k x_i x_k + W^2
      x_i (1 - x_j) = x_i - x_i x_j (penalizes choosing i without prerequisite j)
    """
    n = len(values)
    Q = np.zeros((n, n), dtype=float)
    
    max_v = max(values) if values else 100.0
    min_w = min(weights) if weights else 1.0
    
    # Calibrated penalty factors
    if budget_penalty_weight is None:
        budget_penalty_weight = float((2.0 * max_v) / (min_w ** 2))
    if prereq_penalty_weight is None:
        prereq_penalty_weight = float(1.8 * max_v)
        
    P_b = budget_penalty_weight
    P_p = prereq_penalty_weight
    
    # Diagonal (linear terms in x_i since x_i^2 = x_i for binary variables)
    for i in range(n):
        # Value objective (negated for minimization)
        q_ii = -values[i]
        # Quadratic budget expansion linear term: P_b * (w_i^2 - 2 * capacity * w_i)
        q_ii += P_b * (weights[i] ** 2 - 2.0 * capacity * weights[i])
        Q[i, i] = q_ii
        
    # Prerequisite linear penalties: if activity i requires j, adding i adds P_p
    for (prereq_j, target_i) in prereq_pairs:
        if 0 <= target_i < n and 0 <= prereq_j < n:
            Q[target_i, target_i] += P_p
            
    # Off-diagonal quadratic interaction terms (i < k)
    for i in range(n):
        for k in range(i + 1, n):
            # Budget cross-product term: 2 * P_b * w_i * w_k
            Q[i, k] += 2.0 * P_b * weights[i] * weights[k]
            
    # Prerequisite cross terms: subtract P_p * x_i * x_j
    for (prereq_j, target_i) in prereq_pairs:
        if 0 <= target_i < n and 0 <= prereq_j < n:
            low = min(prereq_j, target_i)
            high = max(prereq_j, target_i)
            Q[low, high] -= P_p
            
    constant_offset = P_b * (capacity ** 2)
    return Q, constant_offset


def qubo_to_ising(Q: np.ndarray, offset: float) -> Tuple[np.ndarray, Dict[Tuple[int, int], float], float]:
    """
    Converts QUBO formulation Q to Ising spin Hamiltonian:
      x_i = (1 - Z_i) / 2
      
    Returns:
      h_coeffs: 1D array of single-qubit Z coefficients
      j_coeffs: dict {(i, j): J_ij} for two-qubit ZZ interaction terms (i < j)
      ising_offset: scalar energy shift
    """
    n = Q.shape[0]
    h_coeffs = np.zeros(n, dtype=float)
    j_coeffs = {}
    ising_offset = offset
    
    # Diagonal contributions
    for i in range(n):
        q_ii = Q[i, i]
        ising_offset += 0.5 * q_ii
        h_coeffs[i] -= 0.5 * q_ii
        
    # Off-diagonal contributions
    for i in range(n):
        for j in range(i + 1, n):
            q_ij = Q[i, j]
            if abs(q_ij) > 1e-9:
                ising_offset += 0.25 * q_ij
                h_coeffs[i] -= 0.25 * q_ij
                h_coeffs[j] -= 0.25 * q_ij
                j_coeffs[(i, j)] = 0.25 * q_ij
                
    return h_coeffs, j_coeffs, ising_offset


def evaluate_solution(
    bitstring: str,
    values: List[float],
    weights: List[float],
    capacity: float,
    prereq_pairs: List[Tuple[int, int]]
) -> Dict[str, Any]:
    """
    Evaluates total value, total hours, and feasibility of a binary selection bitstring.
    Bitstring is little-endian indexed: qubit i is at bit index (len - 1 - i).
    """
    n = len(values)
    selected_indices = []
    for i in range(n):
        char_idx = len(bitstring) - 1 - i
        if char_idx >= 0 and bitstring[char_idx] == '1':
            selected_indices.append(i)
            
    total_value = sum(values[i] for i in selected_indices)
    total_hours = sum(weights[i] for i in selected_indices)
    
    # Feasibility checks
    budget_ok = total_hours <= (capacity + 1e-5)
    
    prereqs_ok = True
    missing_prereqs = []
    selected_set = set(selected_indices)
    for (prereq_j, target_i) in prereq_pairs:
        if target_i in selected_set and prereq_j not in selected_set:
            prereqs_ok = False
            missing_prereqs.append((prereq_j, target_i))
            
    is_feasible = budget_ok and prereqs_ok
    
    return {
        'selected_indices': selected_indices,
        'total_value': round(total_value, 2),
        'total_hours': round(total_hours, 2),
        'budget_ok': budget_ok,
        'prereqs_ok': prereqs_ok,
        'is_feasible': is_feasible,
        'missing_prereqs': missing_prereqs,
    }


def repair_solution(
    initial_indices: List[int],
    values: List[float],
    weights: List[float],
    capacity: float,
    prereq_pairs: List[Tuple[int, int]]
) -> Dict[str, Any]:
    """
    Deterministic Feasibility Repair & Capacity Maximizer.
    
    Guarantees output plan is 100% feasible:
    1. Satisfies all prerequisite dependencies: if target activity i is kept, prerequisite j is ensured;
       if j cannot fit in budget, i is removed.
    2. Enforces strict budget constraint: if total_hours > capacity, items with lowest
       efficiency (value / hour) are iteratively removed.
    3. Greedy pack: if remaining budget allows, unselected activities with fulfilled prerequisites
       and highest efficiency are added.
    """
    n = len(values)
    current = set(initial_indices)
    
    # Helper: get all prerequisites for an item
    prereq_map = {}
    for (p, t) in prereq_pairs:
        prereq_map.setdefault(t, set()).add(p)
        
    # Helper: calculate efficiency ratio (v_i / w_i)
    efficiency = [values[i] / max(0.1, weights[i]) for i in range(n)]
    
    # 1. Prerequisite Resolution
    # If item has prerequisites not in set, attempt to add them if budget permits, else drop item
    changed = True
    while changed:
        changed = False
        for item in list(current):
            needed = prereq_map.get(item, set())
            unmet = needed - current
            if unmet:
                # Can we add all unmet prerequisites without exceeding capacity?
                additional_cost = sum(weights[p] for p in unmet)
                cur_cost = sum(weights[i] for i in current)
                if cur_cost + additional_cost <= capacity + 1e-5:
                    current.update(unmet)
                    changed = True
                else:
                    # Cannot afford prerequisite; must drop dependent item
                    current.remove(item)
                    changed = True
                    
    # 2. Budget Enforcement: remove lowest efficiency items if over capacity
    while sum(weights[i] for i in current) > capacity + 1e-5 and current:
        # Find removable item: an item that is NOT a prerequisite for another selected item,
        # or if all are prerequisites, remove the leaf of the dependency tree with lowest efficiency
        dependents_map = {}
        for (p, t) in prereq_pairs:
            if t in current and p in current:
                dependents_map.setdefault(p, set()).add(t)
                
        # Candidate items for removal: items with no dependents in current set
        removable = [i for i in current if len(dependents_map.get(i, set())) == 0]
        if not removable:
            removable = list(current)
            
        # Pick the lowest efficiency item
        worst_item = min(removable, key=lambda idx: efficiency[idx])
        current.remove(worst_item)
        
        # In case removing it invalidated any remaining items that depended on it:
        for item in list(current):
            if worst_item in prereq_map.get(item, set()):
                current.remove(item)

    # 3. Greedy Pack: utilize remaining capacity with best available valid items
    remaining_budget = capacity - sum(weights[i] for i in current)
    unselected = [i for i in range(n) if i not in current]
    # Sort unselected by efficiency descending
    unselected.sort(key=lambda idx: efficiency[idx], reverse=True)
    
    for candidate in unselected:
        needed_prereqs = prereq_map.get(candidate, set())
        unmet_prereqs = needed_prereqs - current
        total_needed_cost = weights[candidate] + sum(weights[p] for p in unmet_prereqs)
        
        if total_needed_cost <= remaining_budget + 1e-5:
            current.add(candidate)
            current.update(unmet_prereqs)
            remaining_budget -= total_needed_cost
            
    final_indices = sorted(list(current))
    final_value = sum(values[i] for i in final_indices)
    final_hours = sum(weights[i] for i in final_indices)
    
    # Final sanity check
    prereqs_ok = True
    for (p, t) in prereq_pairs:
        if t in current and p not in current:
            prereqs_ok = False
            
    return {
        'selected_indices': final_indices,
        'total_value': round(final_value, 2),
        'total_hours': round(final_hours, 2),
        'is_feasible': (final_hours <= capacity + 1e-5) and prereqs_ok,
    }


def solve_classical_knapsack(
    values: List[float],
    weights: List[float],
    capacity: float,
    prereq_pairs: List[Tuple[int, int]]
) -> Dict[str, Any]:
    """
    Exact Classical Benchmark Solver for Constrained Knapsack with Prerequisites.
    Explores branch-and-bound / state enumeration for N <= 12 to find the provably
    optimal classical baseline solution.
    """
    start_time = time.time()
    n = len(values)
    
    best_value = 0.0
    best_hours = 0.0
    best_indices = []
    
    prereq_map = {}
    for (p, t) in prereq_pairs:
        prereq_map.setdefault(t, set()).add(p)
        
    # Enumerate all 2^n binary configurations (for N <= 12, max 4096 checks)
    total_states = 1 << n
    for mask in range(total_states):
        cur_hours = 0.0
        cur_val = 0.0
        cur_selected = []
        valid = True
        
        for i in range(n):
            if (mask >> i) & 1:
                cur_hours += weights[i]
                if cur_hours > capacity:
                    valid = False
                    break
                cur_val += values[i]
                cur_selected.append(i)
                
        if not valid:
            continue
            
        # Check prerequisites
        selected_set = set(cur_selected)
        for item in cur_selected:
            if not prereq_map.get(item, set()).issubset(selected_set):
                valid = False
                break
                
        if valid and cur_val > best_value:
            best_value = cur_val
            best_hours = cur_hours
            best_indices = cur_selected
            
    exec_time_ms = round((time.time() - start_time) * 1000, 2)
    
    return {
        'algorithm': 'Classical_Exact_BranchAndBound',
        'selected_indices': best_indices,
        'total_value': round(best_value, 2),
        'total_hours': round(best_hours, 2),
        'execution_time_ms': exec_time_ms,
        'is_optimal': True,
    }


def run_qaoa_optimization(
    activities: List[Dict[str, Any]],
    total_hours_budget: float,
    priority_areas: Optional[List[str]] = None,
    max_qubits: int = MAX_QAOA_QUBITS,
    p_layers: int = 1
) -> Dict[str, Any]:
    """
    Executes QAOA Quantum Approximate Optimization Algorithm on the candidate's activity pool.
    
    Pipeline:
    1. Filter & rank top candidate activities up to max_qubits (retaining prerequisite integrity)
    2. Calculate normalized multi-objective values v_i and study hours w_i
    3. Construct QUBO and Ising spin Hamiltonian coefficients (h_i, J_ij)
    4. Build parameterized QAOA quantum circuit (Hadamards, U(H_C, gamma), U(H_M, beta))
    5. Optimize variational parameters using classical COBYLA minimizer on Qiskit Statevector
    6. Measure probability distribution, extract top bitstring, test feasibility
    7. Apply deterministic repair algorithm to enforce capacity and prerequisite integrity
    8. Execute classical exact benchmark solver on the identical instance for scientific comparison
    """
    overall_start_time = time.time()
    
    if not activities:
        return {
            'success': False,
            'error': 'No activities provided for optimization',
            'algorithm_used': 'None',
        }
        
    # 1. Candidate Selection for Quantum Register Sizing
    # Sort candidate activities by priority, severity, and relevance to select top N qubits
    # Ensure any prerequisite topics are included in the pool
    activity_id_to_idx = {act['id']: i for i, act in enumerate(activities)}
    
    # Calculate preliminary scores for ranking
    scored_pool = []
    for act in activities:
        val = calculate_activity_value(act, priority_areas)
        scored_pool.append((val, act))
        
    # Sort descending by value
    scored_pool.sort(key=lambda x: x[0], reverse=True)
    
    selected_acts = []
    selected_ids = set()
    
    for _, act in scored_pool:
        if len(selected_acts) >= max_qubits:
            break
        if act['id'] not in selected_ids:
            selected_acts.append(act)
            selected_ids.add(act['id'])
            # Check if prerequisites should be pulled in
            for prereq_id in act.get('prerequisites', []):
                if prereq_id in activity_id_to_idx and prereq_id not in selected_ids:
                    if len(selected_acts) < max_qubits:
                        prereq_act = activities[activity_id_to_idx[prereq_id]]
                        selected_acts.append(prereq_act)
                        selected_ids.add(prereq_id)
                        
    n_qubits = len(selected_acts)
    act_id_map = {act['id']: i for i, act in enumerate(selected_acts)}
    
    # Build prerequisite index pairs within this selected set
    prereq_pairs = []
    for target_idx, act in enumerate(selected_acts):
        for p_id in act.get('prerequisites', []):
            if p_id in act_id_map:
                prereq_pairs.append((act_id_map[p_id], target_idx))
                
    # Extract values and weights
    values = [calculate_activity_value(act, priority_areas) for act in selected_acts]
    weights = [float(act.get('estimated_study_hours', 2.0)) for act in selected_acts]
    capacity = float(total_hours_budget)
    
    # Execute Classical Exact Benchmark on identical instance
    classical_benchmark = solve_classical_knapsack(values, weights, capacity, prereq_pairs)
    
    # Check if Qiskit is available
    if not QISKIT_AVAILABLE:
        logger.warning("Qiskit not installed. Falling back directly to classical solver.")
        repaired = repair_solution(classical_benchmark['selected_indices'], values, weights, capacity, prereq_pairs)
        return {
            'success': True,
            'algorithm_used': 'Classical_BranchAndBound_Fallback',
            'is_quantum': False,
            'selected_activities': [selected_acts[i] for i in repaired['selected_indices']],
            'selected_indices': repaired['selected_indices'],
            'total_value': repaired['total_value'],
            'total_hours': repaired['total_hours'],
            'budget_capacity': capacity,
            'num_qubits': n_qubits,
            'classical_comparison': classical_benchmark,
            'execution_time_ms': round((time.time() - overall_start_time) * 1000, 2),
            'metadata': {
                'reason': 'Qiskit not installed',
                'repaired': False,
            }
        }
        
    # 2. Build QUBO Matrix and Ising Coefficients
    Q, const_offset = build_qubo_matrix(values, weights, capacity, prereq_pairs)
    h_coeffs, j_coeffs, ising_offset = qubo_to_ising(Q, const_offset)
    
    # Normalize Ising coefficients for numerical stability during parameter sweeps
    norm_factor = max(1.0, np.max(np.abs(h_coeffs)), *(abs(v) for v in j_coeffs.values()) if j_coeffs else [1.0])
    h_scaled = h_coeffs / norm_factor
    j_scaled = {k: v / norm_factor for k, v in j_coeffs.items()}
    
    # Precompute energy lookup table for all 2^n states to achieve ultra-fast objective evaluation
    num_states = 1 << n_qubits
    energy_table = np.zeros(num_states, dtype=float)
    for state_int in range(num_states):
        # Convert state_int to binary vector
        x_vec = [(state_int >> i) & 1 for i in range(n_qubits)]
        # Evaluate QUBO cost
        x_np = np.array(x_vec, dtype=float)
        cost = np.dot(x_np, np.dot(Q, x_np)) + const_offset
        energy_table[state_int] = cost
        
    circuit_depth = 0
    qaoa_start_time = time.time()
    
    # 3. QAOA Circuit Generator
    def construct_qaoa_circuit(params):
        qc = QuantumCircuit(n_qubits)
        # Uniform superposition
        for i in range(n_qubits):
            qc.h(i)
            
        # Layers of Cost and Mixer unitaries
        for layer in range(p_layers):
            gamma = params[layer]
            beta = params[p_layers + layer]
            
            # Problem Unitary U(H_C, gamma)
            for i in range(n_qubits):
                if abs(h_scaled[i]) > 1e-6:
                    qc.rz(2.0 * gamma * h_scaled[i], i)
            for (i, j), j_val in j_scaled.items():
                if abs(j_val) > 1e-6:
                    qc.rzz(2.0 * gamma * j_val, i, j)
                    
            # Mixer Unitary U(H_M, beta)
            for i in range(n_qubits):
                qc.rx(2.0 * beta, i)
                
        return qc
        
    # Measure sample circuit depth for metadata reporting
    sample_qc = construct_qaoa_circuit([0.5] * p_layers + [0.5] * p_layers)
    circuit_depth = sample_qc.depth()
    
    # 4. Energy Expectation Objective Function
    eval_count = 0
    def objective_function(params):
        nonlocal eval_count
        eval_count += 1
        qc = construct_qaoa_circuit(params)
        sv = Statevector.from_instruction(qc)
        # Vectorized expectation value over statevector probabilities
        probs = sv.probabilities()
        expected_energy = float(np.dot(probs, energy_table))
        return expected_energy
        
    # 5. Variational Optimization using Classical COBYLA Minimizer
    initial_params = [0.35 * (l + 1) for l in range(p_layers)] + [0.45 * (l + 1) for l in range(p_layers)]
    try:
        opt_res = minimize(
            objective_function,
            initial_params,
            method='COBYLA',
            options={'maxiter': 35, 'tol': 1e-3}
        )
        optimal_params = opt_res.x.tolist()
        opt_success = opt_res.success
    except Exception as exc:
        logger.warning(f"QAOA parameter optimization encountered error: {exc}. Using initial parameters.")
        optimal_params = initial_params
        opt_success = False
        
    qaoa_circuit_time_ms = round((time.time() - qaoa_start_time) * 1000, 2)
    
    # 6. Sample Optimal Statevector Probabilities
    optimal_qc = construct_qaoa_circuit(optimal_params)
    optimal_sv = Statevector.from_instruction(optimal_qc)
    prob_dict = optimal_sv.probabilities_dict()
    
    # Sort bitstrings by probability descending
    sorted_candidates = sorted(prob_dict.items(), key=lambda kv: kv[1], reverse=True)
    
    # Inspect top-k candidate bitstrings
    top_candidates = []
    best_raw_candidate = None
    best_raw_eval = None
    
    for bstring, prob in sorted_candidates[:5]:
        eval_info = evaluate_solution(bstring, values, weights, capacity, prereq_pairs)
        candidate_entry = {
            'bitstring': bstring,
            'probability': round(float(prob), 4),
            'value': eval_info['total_value'],
            'hours': eval_info['total_hours'],
            'is_feasible': eval_info['is_feasible'],
        }
        top_candidates.append(candidate_entry)
        
        if best_raw_candidate is None:
            best_raw_candidate = bstring
            best_raw_eval = eval_info
        elif eval_info['is_feasible'] and not best_raw_eval['is_feasible']:
            # Prefer a feasible raw bitstring if found in top samples
            best_raw_candidate = bstring
            best_raw_eval = eval_info
            
    # 7. Apply Deterministic Feasibility Repair
    raw_indices = best_raw_eval['selected_indices']
    was_raw_feasible = best_raw_eval['is_feasible']
    
    repaired_result = repair_solution(
        raw_indices,
        values,
        weights,
        capacity,
        prereq_pairs
    )
    
    final_indices = repaired_result['selected_indices']
    final_value = repaired_result['total_value']
    final_hours = repaired_result['total_hours']
    
    # Map selected indices back to structured activity objects
    selected_activities = [selected_acts[i] for i in final_indices]
    
    # Approximation ratio compared to classical theoretical optimum
    classical_opt_val = classical_benchmark['total_value']
    if classical_opt_val > 0:
        approx_ratio = round(min(1.0, final_value / classical_opt_val), 3)
    else:
        approx_ratio = 1.0
        
    total_pipeline_time_ms = round((time.time() - overall_start_time) * 1000, 2)
    
    return {
        'success': True,
        'algorithm_used': f'QAOA_Statevector_p{p_layers}',
        'is_quantum': True,
        'selected_activities': selected_activities,
        'selected_indices': final_indices,
        'total_value': final_value,
        'total_hours': final_hours,
        'budget_capacity': capacity,
        'num_qubits': n_qubits,
        'circuit_depth': circuit_depth,
        'p_layers': p_layers,
        'optimal_parameters': {
            'gamma': optimal_params[:p_layers],
            'beta': optimal_params[p_layers:],
        },
        'raw_solution': {
            'bitstring': best_raw_candidate,
            'value': best_raw_eval['total_value'],
            'hours': best_raw_eval['total_hours'],
            'is_feasible': was_raw_feasible,
        },
        'repair_applied': not was_raw_feasible or (final_indices != raw_indices),
        'top_measurement_states': top_candidates[:3],
        'classical_comparison': {
            'classical_algorithm': classical_benchmark['algorithm'],
            'classical_optimal_value': classical_benchmark['total_value'],
            'classical_hours': classical_benchmark['total_hours'],
            'classical_execution_time_ms': classical_benchmark['execution_time_ms'],
            'qaoa_approximation_ratio': approx_ratio,
        },
        'execution_time_ms': total_pipeline_time_ms,
        'qaoa_circuit_time_ms': qaoa_circuit_time_ms,
    }

