"""
Preparation Plan Generator & Multi-Day Timetable Scheduler.

Orchestrates the complete pipeline:
1. Extract candidate strengths, weaknesses, and skill-gap activity pool from interview assessment / profile.
2. Formulate optimization preferences and capacity constraints.
3. Execute QAOA quantum optimization (with automatic deterministic classical fallback).
4. Topologically sequence selected activities according to prerequisite dependency trees.
5. Distribute activities into a realistic multi-day study timetable.
6. Persist PreparationPlan and PracticeModule records to the database.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from decimal import Decimal

from django.db import transaction
from django.utils import timezone as django_tz

from apps.accounts.models import StudentProfile
from apps.resumes.models import TargetRole
from apps.sessions.models import InterviewSession
from apps.preparation.models import PreparationPlan, PracticeModule
from apps.preparation.services.feedback_extractor import extract_feedback_and_activity_pool
from apps.preparation.services.qaoa_optimizer import (
    run_qaoa_optimization,
    solve_classical_knapsack,
    calculate_activity_value,
    repair_solution
)

logger = logging.getLogger(__name__)


def schedule_activities_into_days(
    activities: List[Dict[str, Any]],
    days_remaining: int,
    daily_hours: float
) -> List[Dict[str, Any]]:
    """
    Topologically schedules activities across available preparation days.
    
    Ensures:
    1. Prerequisites appear on the same or earlier day as dependent topics.
    2. Daily hours do not excessively exceed candidate daily capacity.
    3. Practice modules are assigned consistent sequential day and order indices.
    """
    if not activities:
        return []
        
    days_count = max(1, days_remaining)
    daily_cap = max(0.5, float(daily_hours))
    
    # 1. Topological ordering respecting prerequisites
    id_to_act = {act['id']: act for act in activities}
    selected_ids = set(id_to_act.keys())
    
    visited = set()
    ordered_acts = []
    
    def visit(act_id: str):
        if act_id in visited or act_id not in id_to_act:
            return
        # Visit prerequisites first
        for prereq in id_to_act[act_id].get('prerequisites', []):
            if prereq in selected_ids and prereq not in visited:
                visit(prereq)
        visited.add(act_id)
        ordered_acts.append(id_to_act[act_id])
        
    for act in activities:
        visit(act['id'])
        
    # 2. Greedy day bin-packing
    scheduled = []
    current_day = 1
    current_day_hours = 0.0
    current_day_order = 1
    
    # Mapping to keep track of when prerequisites were scheduled
    scheduled_day_map = {}
    
    for act in ordered_acts:
        act_hours = float(act.get('estimated_study_hours', 2.0))
        
        # Prerequisite day constraint: current_day cannot be earlier than any prerequisite's day
        prereqs = act.get('prerequisites', [])
        min_allowed_day = 1
        for p in prereqs:
            if p in scheduled_day_map:
                min_allowed_day = max(min_allowed_day, scheduled_day_map[p])
                
        if current_day < min_allowed_day:
            current_day = min_allowed_day
            current_day_hours = 0.0
            current_day_order = 1
            
        # Check if adding this activity exceeds daily capacity significantly (30% margin)
        if current_day_hours + act_hours > (daily_cap * 1.30) and current_day < days_count:
            current_day += 1
            current_day_hours = 0.0
            current_day_order = 1
            
        scheduled_entry = {
            'activity': act,
            'scheduled_day': current_day,
            'order': current_day_order,
            'estimated_hours': act_hours,
        }
        scheduled.append(scheduled_entry)
        scheduled_day_map[act['id']] = current_day
        
        current_day_hours += act_hours
        current_day_order += 1
        
    return scheduled


def generate_preparation_plan(
    student_profile: StudentProfile,
    session: Optional[InterviewSession] = None,
    target_role_id: Optional[str] = None,
    days_remaining: int = 7,
    daily_hours: float = 2.0,
    total_hours_budget: Optional[float] = None,
    priority_areas: Optional[List[str]] = None,
    preferred_categories: Optional[List[str]] = None,
    force_algorithm: Optional[str] = None
) -> PreparationPlan:
    """
    Primary API service function to generate and persist a QAOA personalized preparation plan.
    
    Workflow:
    1. Feedback extraction from mock interview (or resume cold-start)
    2. QAOA / Knapsack optimization with budget and prerequisite constraints
    3. Multi-day study schedule construction
    4. Atomic database persistence of PreparationPlan and PracticeModule records
    """
    days_remaining = max(1, int(days_remaining))
    daily_hours = max(0.5, float(daily_hours))
    
    if total_hours_budget is None:
        total_hours_budget = float(days_remaining * daily_hours)
    else:
        total_hours_budget = max(1.0, float(total_hours_budget))
        
    if priority_areas is None:
        priority_areas = []
        
    # Resolve target role
    target_role = None
    if target_role_id:
        target_role = TargetRole.objects.filter(id=target_role_id).first()
    if not target_role and session and session.target_role:
        target_role = session.target_role
    if not target_role:
        # Fallback to student's most recent active resume role
        latest_resume = student_profile.resumes.filter(is_active=True).first()
        if latest_resume and latest_resume.target_role:
            target_role = latest_resume.target_role
            
    # 1. Extract Structured Feedback and Activity Pool
    feedback_data = extract_feedback_and_activity_pool(
        student_profile=student_profile,
        session=session,
        target_role=target_role
    )
    
    activity_pool = feedback_data['activity_pool']
    
    # Filter by preferred categories if explicitly provided
    if preferred_categories:
        pref_cats = [c.lower().strip() for c in preferred_categories]
        filtered_pool = [a for a in activity_pool if a.get('category', '').lower() in pref_cats]
        # Only use filtered pool if it has adequate choices
        if len(filtered_pool) >= 3:
            activity_pool = filtered_pool
            
    # 2. Run Optimization (QAOA or Classical Fallback)
    opt_result = None
    if force_algorithm == 'classical':
        # Pure classical branch and bound
        values = [calculate_activity_value(act, priority_areas) for act in activity_pool]
        weights = [float(act.get('estimated_study_hours', 2.0)) for act in activity_pool]
        act_id_map = {act['id']: i for i, act in enumerate(activity_pool)}
        prereq_pairs = []
        for t_idx, act in enumerate(activity_pool):
            for p in act.get('prerequisites', []):
                if p in act_id_map:
                    prereq_pairs.append((act_id_map[p], t_idx))
                    
        classical_sol = solve_classical_knapsack(values, weights, total_hours_budget, prereq_pairs)
        repaired = repair_solution(classical_sol['selected_indices'], values, weights, total_hours_budget, prereq_pairs)
        
        opt_result = {
            'success': True,
            'algorithm_used': 'Classical_Exact_BranchAndBound',
            'is_quantum': False,
            'selected_activities': [activity_pool[i] for i in repaired['selected_indices']],
            'selected_indices': repaired['selected_indices'],
            'total_value': repaired['total_value'],
            'total_hours': repaired['total_hours'],
            'budget_capacity': total_hours_budget,
            'num_qubits': len(activity_pool),
            'circuit_depth': 0,
            'p_layers': 0,
            'repair_applied': False,
            'classical_comparison': classical_sol,
            'execution_time_ms': classical_sol['execution_time_ms'],
        }
    else:
        # Run genuine QAOA on quantum circuit
        try:
            opt_result = run_qaoa_optimization(
                activities=activity_pool,
                total_hours_budget=total_hours_budget,
                priority_areas=priority_areas,
                max_qubits=10,
                p_layers=1
            )
        except Exception as exc:
            logger.exception(f"QAOA run failed with exception: {exc}. Executing classical fallback.")
            values = [calculate_activity_value(act, priority_areas) for act in activity_pool]
            weights = [float(act.get('estimated_study_hours', 2.0)) for act in activity_pool]
            act_id_map = {act['id']: i for i, act in enumerate(activity_pool)}
            prereq_pairs = []
            for t_idx, act in enumerate(activity_pool):
                for p in act.get('prerequisites', []):
                    if p in act_id_map:
                        prereq_pairs.append((act_id_map[p], t_idx))
            classical_sol = solve_classical_knapsack(values, weights, total_hours_budget, prereq_pairs)
            repaired = repair_solution(classical_sol['selected_indices'], values, weights, total_hours_budget, prereq_pairs)
            opt_result = {
                'success': True,
                'algorithm_used': 'Classical_BranchAndBound_Fallback',
                'is_quantum': False,
                'selected_activities': [activity_pool[i] for i in repaired['selected_indices']],
                'selected_indices': repaired['selected_indices'],
                'total_value': repaired['total_value'],
                'total_hours': repaired['total_hours'],
                'budget_capacity': total_hours_budget,
                'num_qubits': len(activity_pool),
                'circuit_depth': 0,
                'p_layers': 0,
                'repair_applied': True,
                'classical_comparison': classical_sol,
                'execution_time_ms': classical_sol['execution_time_ms'],
                'error_detail': str(exc),
            }

    selected_activities = opt_result.get('selected_activities', [])
    
    # 3. Schedule Selected Activities Into Daily Timetable
    scheduled_schedule = schedule_activities_into_days(
        activities=selected_activities,
        days_remaining=days_remaining,
        daily_hours=daily_hours
    )
    
    # 4. Format Topic Weights and Recommended Sequence for DB JSONFields
    topic_weights = {}
    for act in selected_activities:
        val = calculate_activity_value(act, priority_areas)
        topic_weights[act['topic']] = round(val / 100.0, 2)
        
    recommended_sequence = []
    for item in scheduled_schedule:
        act = item['activity']
        seq_entry = {
            'day': item['scheduled_day'],
            'order': item['order'],
            'topic': act['topic'],
            'title': act['title'],
            'hours': item['estimated_hours'],
            'category': act['category'],
            'priority': act['priority'],
            'why_selected': act['why_selected'],
            'expected_outcome': act['expected_outcome'],
            'practice_question_types': act.get('practice_exercises', []),
            'sub_topics': act.get('recommended_activities', []),
        }
        recommended_sequence.append(seq_entry)
        
    # Compile comprehensive feedback summary
    feedback_summary = {
        'has_mock_interview': feedback_data['has_mock_interview'],
        'session_id': feedback_data['session_id'],
        'target_role': feedback_data['target_role'],
        'interview_metrics': feedback_data.get('interview_metrics', {}),
        'strong_areas': feedback_data.get('strong_areas', []),
        'weak_areas': feedback_data.get('weak_areas', []),
        'strengths': feedback_data['strengths'],
        'weaknesses': feedback_data['weaknesses'],
        'disclaimer': feedback_data['disclaimer'],
        'total_activities_evaluated': len(activity_pool),
        'total_activities_selected': len(selected_activities),
    }
    
    # Optimization metadata dictionary
    optimization_metadata = {
        'algorithm_used': opt_result.get('algorithm_used', 'qaoa'),
        'is_quantum': opt_result.get('is_quantum', True),
        'num_qubits': opt_result.get('num_qubits', len(selected_activities)),
        'circuit_depth': opt_result.get('circuit_depth', 0),
        'p_layers': opt_result.get('p_layers', 1),
        'execution_time_ms': opt_result.get('execution_time_ms', 0),
        'qaoa_circuit_time_ms': opt_result.get('qaoa_circuit_time_ms', 0),
        'total_value': opt_result.get('total_value', 0),
        'total_hours': opt_result.get('total_hours', 0),
        'budget_capacity': total_hours_budget,
        'repair_applied': opt_result.get('repair_applied', False),
        'raw_solution': opt_result.get('raw_solution', {}),
        'top_measurement_states': opt_result.get('top_measurement_states', []),
        'classical_comparison': opt_result.get('classical_comparison', {}),
        'optimal_parameters': opt_result.get('optimal_parameters', {}),
    }
    
    # 5. Persist Atomically to Database
    with transaction.atomic():
        # Deactivate previous active plans for this student
        PreparationPlan.objects.filter(
            student=student_profile,
            is_active=True
        ).update(is_active=False)
        
        plan = PreparationPlan.objects.create(
            student=student_profile,
            target_role=target_role,
            session=session,
            preparation_days=days_remaining,
            total_hours_budget=total_hours_budget,
            daily_hours=daily_hours,
            algorithm_used=opt_result.get('algorithm_used', 'qaoa'),
            topic_weights=topic_weights,
            recommended_sequence=recommended_sequence,
            feedback_summary=feedback_summary,
            priority_areas=priority_areas,
            optimization_metadata=optimization_metadata,
            circuit_depth=opt_result.get('circuit_depth'),
            qaoa_energy=opt_result.get('raw_solution', {}).get('value'),
            is_active=True
        )
        
        # Create PracticeModule objects
        module_instances = []
        for item in scheduled_schedule:
            act = item['activity']
            mod = PracticeModule(
                plan=plan,
                student=student_profile,
                activity_id=act['id'],
                topic=act['topic'],
                sub_topics=act.get('recommended_activities', []),
                scheduled_day=item['scheduled_day'],
                estimated_hours=Decimal(str(item['estimated_hours'])),
                priority=act.get('priority', 'medium'),
                why_selected=act.get('why_selected', ''),
                expected_outcome=act.get('expected_outcome', ''),
                practice_exercises=act.get('practice_exercises', []),
                prerequisites=act.get('prerequisites', []),
                order=item['order'],
                status='pending',
            )
            module_instances.append(mod)
            
        PracticeModule.objects.bulk_create(module_instances)
        
    logger.info(
        f"Generated QAOA PreparationPlan {plan.id} for student {student_profile.id}: "
        f"{len(module_instances)} modules across {days_remaining} days ({opt_result.get('total_hours')} hrs)."
    )
    
    return plan

