"""
Feedback Analysis & Structured Activity Extractor for QAOA Optimization.

Extracts candidate weaknesses, strengths, and role requirements from:
1. Completed InterviewSession turns, responses, and expected concepts
2. Coding phase submissions & problem-solving test results
3. Multi-modal assessment report & SkillGap models
4. Candidate resume skills & target job role

Outputs structured, validated activity records formatted for binary knapsack / QUBO optimization.
Guarantees genuine, uninflated evaluation: unanswered questions and silence score 0%.
"""
import logging
import re
from typing import Dict, Any, List, Optional
from decimal import Decimal

from apps.accounts.models import StudentProfile
from apps.resumes.models import TargetRole, Resume
from apps.sessions.models import InterviewSession, StudentResponse, InterviewQuestion
from apps.assessments.models import Assessment, SkillGap, CodingSubmission
from apps.assessments.services.report_generator import generate_assessment_report

logger = logging.getLogger(__name__)

# Noise tokens that do not constitute a real answer
_NOISE_TOKENS = frozenset({
    'uh', 'um', 'er', 'hmm', 'hm', 'ah', 'oh', 'okay', 'ok',
    'yeah', 'yes', 'no', 'yep', 'nope', 'right', 'sure', 'fine',
})


def _is_meaningful(text: str) -> bool:
    """Deterministically check if text has substantive candidate answer content."""
    if not text:
        return False
    clean = re.sub(r"[^\w\s']", ' ', text.lower()).strip()
    if not clean:
        return False
    tokens = [t for t in clean.split() if t]
    meaningful = [t for t in tokens if t not in _NOISE_TOKENS and len(t) > 1]
    return len(meaningful) >= 3


# Standard curriculum catalogue mapping topic keys to rich meta-information
TOPIC_CURRICULUM = {
    'arrays_hashing': {
        'topic': 'Arrays & Hashing',
        'title': 'Array Manipulation, Frequency Maps & Hash Tables',
        'category': 'coding',
        'default_hours': 2.5,
        'prerequisites': [],
        'exercises': ['two-sum', 'valid-anagram', 'contains-duplicate'],
        'activities': [
            'Practice constant-time key lookups and collision mitigation',
            'Solve prefix-sum and frequency counter problems',
        ],
        'outcome': 'Confidently manipulate contiguous memory and use hash maps for O(1) lookups.',
        'keywords': ['array', 'hash', 'dictionary', 'map', 'lookup', 'index', 'python', 'java', 'cpp'],
    },
    'two_pointers_sliding_window': {
        'topic': 'Two Pointers & Sliding Window',
        'title': 'Two Pointers and Sliding Window Optimization',
        'category': 'coding',
        'default_hours': 3.0,
        'prerequisites': ['arrays_hashing'],
        'exercises': ['best-time-to-buy-and-sell-stock', 'valid-palindrome', 'longest-substring'],
        'activities': [
            'Optimize nested loop searches to linear O(n) passes',
            'Implement dynamic window sizing for substring challenges',
        ],
        'outcome': 'Identify linear time two-pointer and sliding window opportunities.',
        'keywords': ['pointer', 'window', 'substring', 'subarray', 'range', 'search'],
    },
    'linked_lists_stacks_queues': {
        'topic': 'Linked Lists, Stacks & Queues',
        'title': 'Linear Data Structures, Monotonic Stacks & Queues',
        'category': 'coding',
        'default_hours': 2.5,
        'prerequisites': [],
        'exercises': ['reverse-linked-list', 'valid-parentheses', 'min-stack'],
        'activities': [
            'Practice in-place pointer reversal and sentinel nodes',
            'Implement LIFO and FIFO evaluation pipelines',
        ],
        'outcome': 'Master pointer rewiring, stack backtracking, and queue scheduling.',
        'keywords': ['stack', 'queue', 'linked list', 'lifo', 'fifo', 'node'],
    },
    'binary_trees_bfs_dfs': {
        'topic': 'Binary Trees & Tree Traversals',
        'title': 'Binary Trees, Level-Order BFS & Recursive DFS',
        'category': 'coding',
        'default_hours': 3.5,
        'prerequisites': ['linked_lists_stacks_queues'],
        'exercises': ['maximum-depth-of-binary-tree', 'invert-binary-tree', 'binary-tree-level-order'],
        'activities': [
            'Implement recursive tree traversal patterns (Pre/In/Post)',
            'Construct queue-based level order breadth-first searches',
        ],
        'outcome': 'Solve recursive branch division and level-order state synchronization.',
        'keywords': ['tree', 'binary tree', 'traversal', 'bfs', 'dfs', 'recursion', 'bst'],
    },
    'graphs_topological_sort': {
        'topic': 'Graph Algorithms & Connectivity',
        'title': 'Graph Representations, Cycle Detection & Topological Sort',
        'category': 'coding',
        'default_hours': 4.0,
        'prerequisites': ['binary_trees_bfs_dfs'],
        'exercises': ['number-of-islands', 'course-schedule', 'clone-graph'],
        'activities': [
            'Construct adjacency list models and visit state tracking',
            'Implement Kahn\'s algorithm and cycle detection for dependency graphs',
        ],
        'outcome': 'Model networked systems and calculate dependencies with topological sorting.',
        'keywords': ['graph', 'vertex', 'edge', 'cycle', 'topological', 'network', 'adjacency'],
    },
    'dynamic_programming': {
        'topic': 'Dynamic Programming & Memoization',
        'title': 'Dynamic Programming State Transitions & Memoization',
        'category': 'coding',
        'default_hours': 4.0,
        'prerequisites': ['binary_trees_bfs_dfs'],
        'exercises': ['climbing-stairs', 'coin-change', 'longest-increasing-subsequence'],
        'activities': [
            'Formulate recursive subproblems and identify overlapping states',
            'Convert top-down memoization into space-optimized bottom-up tabulation',
        ],
        'outcome': 'Recognize optimal substructure and construct polynomial-time DP solutions.',
        'keywords': ['dynamic programming', 'dp', 'memoization', 'tabulation', 'recurrence', 'optimization'],
    },
    'system_design_architecture': {
        'topic': 'System Design & Scalability',
        'title': 'Distributed Architecture, Caching & Load Balancing',
        'category': 'system_design',
        'default_hours': 3.5,
        'prerequisites': [],
        'exercises': ['design-rate-limiter', 'design-url-shortener', 'caching-layer-design'],
        'activities': [
            'Design horizontal scaling architectures with CDN & reverse proxy tiers',
            'Apply Redis caching strategies and cache invalidation policies',
        ],
        'outcome': 'Architect fault-tolerant systems with throughput and latency trade-offs.',
        'keywords': ['system design', 'architecture', 'scalability', 'redis', 'cache', 'microservices', 'load balancer'],
    },
    'database_sql_indexing': {
        'topic': 'Databases & Query Optimization',
        'title': 'Relational Schema Design, Indexing & Query Optimization',
        'category': 'technical',
        'default_hours': 2.5,
        'prerequisites': [],
        'exercises': ['sql-joins-group-by', 'index-query-optimization', 'transaction-isolation'],
        'activities': [
            'Analyze EXPLAIN plans and design composite B-Tree indexes',
            'Master ACID isolation levels and prevent N+1 query patterns',
        ],
        'outcome': 'Optimize database schemas and query execution plans under high concurrency.',
        'keywords': ['sql', 'database', 'postgres', 'mysql', 'indexing', 'query', 'acid', 'transactions'],
    },
    'api_rest_microservices': {
        'topic': 'API Design & Backend Services',
        'title': 'RESTful API Standards, Idempotency & Authentication',
        'category': 'technical',
        'default_hours': 2.0,
        'prerequisites': [],
        'exercises': ['rest-api-design', 'jwt-oauth-auth', 'rate-limiting-middleware'],
        'activities': [
            'Construct clean RESTful resource hierarchies with HTTP status fidelity',
            'Implement JWT token refresh strategies and API rate-limiting middleware',
        ],
        'outcome': 'Design secure, idempotent, and production-grade REST APIs.',
        'keywords': ['api', 'rest', 'http', 'jwt', 'auth', 'endpoint', 'backend', 'microservices'],
    },
    'oop_design_patterns': {
        'topic': 'OOP & Clean Software Architecture',
        'title': 'SOLID Principles, Clean Code & GoF Design Patterns',
        'category': 'technical',
        'default_hours': 2.5,
        'prerequisites': [],
        'exercises': ['factory-singleton-pattern', 'dependency-injection', 'solid-refactor'],
        'activities': [
            'Refactor legacy codebases using SOLID principles',
            'Implement Factory, Observer, Strategy, and Dependency Injection patterns',
        ],
        'outcome': 'Write modular, extensible, and easily testable object-oriented code.',
        'keywords': ['oop', 'object oriented', 'solid', 'design pattern', 'encapsulation', 'polymorphism'],
    },
    'behavioral_star_storytelling': {
        'topic': 'Behavioral Leadership & Communication',
        'title': 'STAR Framework, Conflict Resolution & Behavioral Storytelling',
        'category': 'behavioral',
        'default_hours': 2.0,
        'prerequisites': [],
        'exercises': ['star-conflict-story', 'leadership-under-pressure', 'failure-learning-reflection'],
        'activities': [
            'Structure past project hurdles into Situation-Task-Action-Result format',
            'Refine concise verbal delivery for cultural fit and conflict resolution',
        ],
        'outcome': 'Deliver compelling, metric-driven narrative responses to executive interviewers.',
        'keywords': ['behavioral', 'star', 'communication', 'conflict', 'leadership', 'teamwork', 'culture'],
    },
    'project_deep_dive_metrics': {
        'topic': 'Project Architecture & Technical Justification',
        'title': 'Portfolio Project Deep-Dive & Engineering Trade-Offs',
        'category': 'project',
        'default_hours': 2.5,
        'prerequisites': ['oop_design_patterns'],
        'exercises': ['project-tradeoff-pitch', 'bottleneck-postmortem', 'architecture-whiteboard'],
        'activities': [
            'Document quantitative impact metrics (e.g., latency reduction, user scale)',
            'Prepare defense for chosen tech stack alternatives and design compromises',
        ],
        'outcome': 'Articulate engineering justifications for personal and production projects.',
        'keywords': ['project', 'portfolio', 'resume', 'tradeoff', 'metrics', 'architecture'],
    },
}


def _calculate_role_relevance(topic_data: Dict[str, Any], target_role_name: str, domain: str) -> float:
    """Calculate role relevance multiplier in range [0.20, 1.00] based on target role."""
    combined_target = f"{target_role_name} {domain}".lower()
    keywords = topic_data.get('keywords', [])

    matches = sum(1 for kw in keywords if kw in combined_target)
    if matches >= 3:
        return 0.95
    elif matches >= 2:
        return 0.85
    elif matches == 1:
        return 0.70

    # Domain specific defaults
    category = topic_data.get('category', 'technical')
    if 'software' in combined_target or 'developer' in combined_target or 'engineer' in combined_target:
        if category in ('coding', 'technical', 'system_design'):
            return 0.80
    elif 'data' in combined_target or 'machine learning' in combined_target:
        if topic_data['topic'] in ('Databases & Query Optimization', 'Arrays & Hashing', 'Dynamic Programming'):
            return 0.85
    elif 'product' in combined_target or 'manager' in combined_target:
        if category in ('behavioral', 'system_design', 'project'):
            return 0.90

    return 0.50


def extract_feedback_and_activity_pool(
    student: Optional[StudentProfile] = None,
    session_id: Optional[str] = None,
    target_role_id: Optional[str] = None,
    student_profile: Optional[StudentProfile] = None,
    session: Optional[InterviewSession] = None,
    target_role: Optional[TargetRole] = None,
) -> Dict[str, Any]:
    """
    Extract structured feedback analysis and build candidate preparation activity pool.
    Handles both post-interview students and initial pre-interview cold-start students.
    
    Guarantees:
    - Accurate evaluation: unanswered questions score 0%.
    - Distinct Strong Areas vs Weak Areas sections.
    - Honest feedback based on actual performance.
    """
    student = student or student_profile
    if not student and session:
        student = session.student

    # 1. Determine Target Role
    if not target_role and target_role_id:
        target_role = TargetRole.objects.filter(id=target_role_id, student=student).first()
    if not target_role and session and getattr(session, 'target_role', None):
        target_role = session.target_role
    if not target_role and student:
        target_role = TargetRole.objects.filter(student=student, is_primary=True).first()
    if not target_role and student:
        target_role = TargetRole.objects.filter(student=student).first()

    target_role_name = target_role.role_name if target_role else "Software Engineer"
    target_role_domain = target_role.domain if target_role else "software_engineering"

    # 2. Retrieve Interview Session & Assessment
    assessment: Optional[Assessment] = None

    if not session and session_id and student:
        session = InterviewSession.objects.filter(id=session_id, student=student).first()
    if not session and student:
        session = InterviewSession.objects.filter(
            student=student,
            status__in=['completed', 'active']
        ).order_by('-started_at', '-created_at').first()

    has_mock_interview = False
    strengths: List[str] = []
    weaknesses: List[Dict[str, Any]] = []
    strong_areas: List[Dict[str, Any]] = []
    weak_areas: List[Dict[str, Any]] = []
    topic_performance: Dict[str, float] = {}

    total_questions_asked = 0
    questions_answered_meaningfully = 0
    overall_score_pct = 0

    if session:
        has_mock_interview = True
        # Try to find or generate assessment report
        try:
            assessment = getattr(session, 'assessment', None)
            if not assessment and session.status == 'completed':
                assessment = generate_assessment_report(session)
        except Exception as e:
            logger.warning("Failed to auto-generate assessment for session %s: %s", session.id, e)

        questions = list(session.questions.all())
        responses = list(session.responses.select_related('question').all())
        coding_subs = list(session.coding_submissions.all())

        total_questions_asked = len(questions) or len(responses)
        resp_by_qid = {r.question_id: r for r in responses}

        # Evaluate topic scores accurately
        if questions:
            for q in questions:
                t = (q.topic or 'General').strip()
                t_key = t.lower()

                r = resp_by_qid.get(q.id)
                if r is not None:
                    resp_text = (getattr(r, 'transcript', '') or getattr(r, 'response_text', '') or '').strip()
                    if _is_meaningful(resp_text) and r.score is not None and float(r.score) > 0:
                        questions_answered_meaningfully += 1
                        sc = float(r.score)
                    else:
                        sc = 0.0
                else:
                    # Unanswered question gets 0.0
                    sc = 0.0

                if t_key not in topic_performance:
                    topic_performance[t_key] = sc
                else:
                    topic_performance[t_key] = (topic_performance[t_key] + sc) / 2.0
        else:
            for r in responses:
                t = (r.question.topic if r.question and r.question.topic else 'General').strip()
                t_key = t.lower()
                resp_text = (getattr(r, 'transcript', '') or getattr(r, 'response_text', '') or '').strip()
                if _is_meaningful(resp_text) and r.score is not None and float(r.score) > 0:
                    questions_answered_meaningfully += 1
                    sc = float(r.score)
                else:
                    sc = 0.0
                topic_performance[t_key] = sc

        # Coding submissions
        for cs in coding_subs:
            sc = float(cs.overall_score) if cs.overall_score is not None else 0.0
            topic_performance['coding_problem_solving'] = sc

        if assessment:
            overall_score_pct = int(float(assessment.overall_score) * 100)
            strengths.extend(assessment.strengths[:4])
            for item in assessment.improvement_areas[:6]:
                weaknesses.append({
                    'area': item.get('area', 'Technical Topic'),
                    'priority': item.get('priority', 'medium'),
                    'recommendation': item.get('recommendation', ''),
                })

        # Categorize Strong Areas vs Weak Areas based on real scores
        for t_key, sc in topic_performance.items():
            sc_pct = int(round(sc * 100))
            display_name = t_key.replace('_', ' ').title()

            if sc >= 0.70:
                strong_areas.append({
                    'topic': display_name,
                    'score_pct': sc_pct,
                    'category': 'Verified Competency',
                    'reason': f"Scored {sc_pct}% in mock interview questions.",
                })
            elif sc < 0.60:
                prio = 'high' if sc < 0.40 else 'medium'
                if sc == 0.0:
                    weak_areas.append({
                        'topic': display_name,
                        'score_pct': 0,
                        'priority': 'high',
                        'status': 'unanswered',
                        'reason': 'Question was asked but left unanswered (0%).',
                        'recommendation': f"Practice answering {display_name} questions out loud. Leaving questions blank guarantees zero score in technical rounds.",
                    })
                else:
                    weak_areas.append({
                        'topic': display_name,
                        'score_pct': sc_pct,
                        'priority': prio,
                        'status': 'low_score',
                        'reason': f"Scored {sc_pct}% (below passing threshold).",
                        'recommendation': f"Deepen conceptual fundamentals and problem-solving patterns in {display_name}.",
                    })

    # If no mock interview or weaknesses empty, generate baseline from resume & target role
    if not has_mock_interview or not weaknesses:
        strengths.append(f"Targeting {target_role_name} with verified foundational curriculum requirements.")
        weaknesses.append({
            'area': "Core Algorithmic Problem Solving",
            'priority': 'high',
            'recommendation': "Establish verified baseline mastery in foundational data structures & algorithms.",
        })
        weaknesses.append({
            'area': "System Design Trade-offs",
            'priority': 'medium',
            'recommendation': "Review architectural scalability, caching patterns, and high-concurrency design.",
        })
        weaknesses.append({
            'area': "Behavioral & STAR Delivery",
            'priority': 'medium',
            'recommendation': "Formulate structured scenario examples highlighting leadership and conflict resolution.",
        })

    # 3. Build Structured Activity Pool for QAOA Knapsack
    activity_pool: List[Dict[str, Any]] = []

    for key, curriculum in TOPIC_CURRICULUM.items():
        # Estimate current proficiency score
        matched_score = None
        for test_topic, score_val in topic_performance.items():
            if any(kw in test_topic for kw in curriculum['keywords']):
                matched_score = score_val
                break

        if matched_score is not None:
            # Genuine matched score: if candidate got 0%, cur_score is 0.00!
            cur_score = round(max(0.0, min(1.0, matched_score)), 2)
        else:
            # Check candidate's existing SkillGap records if present
            skill_gap = SkillGap.objects.filter(
                student=student,
                skill_name__icontains=curriculum['topic'].split()[0],
                resolved_at__isnull=True
            ).first()
            if skill_gap:
                cur_score = float(skill_gap.current_level)
            else:
                # Default cold-start baseline: 0.50 technical, 0.60 behavioral
                cur_score = 0.60 if curriculum['category'] == 'behavioral' else 0.50

        target_score = 0.90
        gap_severity = round(max(0.05, target_score - cur_score), 2)
        role_relevance = round(_calculate_role_relevance(curriculum, target_role_name, target_role_domain), 2)

        # Calculate estimated selection impact estimate (normalized 0.10–1.00)
        impact_est = round(min(1.0, (gap_severity * 0.60) + (role_relevance * 0.40)), 2)

        # Determine priority genuinely
        if cur_score == 0.0 and matched_score is not None:
            priority = 'high'
        elif gap_severity >= 0.45 and role_relevance >= 0.70:
            priority = 'high'
        elif gap_severity >= 0.25 or role_relevance >= 0.80:
            priority = 'medium'
        else:
            priority = 'low'

        # Why was this topic selected?
        if has_mock_interview and matched_score is not None:
            if cur_score == 0.0:
                why_selected = "Critical gap: Left completely unanswered (0% score) in your recent mock interview."
            elif cur_score < 0.60:
                why_selected = f"Active improvement area: Scored {int(cur_score*100)}% in your mock interview."
            else:
                why_selected = f"Demonstrated competency: Scored {int(cur_score*100)}% in your interview. Included to reinforce placement mastery."
        else:
            why_selected = f"Essential core competency for {target_role_name} roles."

        activity_item = {
            'id': key,
            'topic': curriculum['topic'],
            'title': curriculum['title'],
            'category': curriculum['category'],
            'current_score': cur_score,
            'target_score': target_score,
            'skill_gap_severity': gap_severity,
            'role_relevance': role_relevance,
            'selection_impact_estimate': impact_est,
            'estimated_study_hours': float(curriculum['default_hours']),
            'priority': priority,
            'why_selected': why_selected,
            'expected_outcome': curriculum['outcome'],
            'recommended_activities': curriculum['activities'],
            'practice_exercises': curriculum['exercises'],
            'prerequisites': curriculum['prerequisites'],
        }
        activity_pool.append(activity_item)

    return {
        'has_mock_interview': has_mock_interview,
        'session_id': str(session.id) if session else None,
        'target_role': {
            'id': str(target_role.id) if target_role else None,
            'role_name': target_role_name,
            'domain': target_role_domain,
        },
        'interview_metrics': {
            'total_questions_asked': total_questions_asked,
            'questions_answered': questions_answered_meaningfully,
            'overall_score_pct': overall_score_pct,
        },
        'strong_areas': strong_areas,
        'weak_areas': weak_areas,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'activity_pool': activity_pool,
        'total_activities_available': len(activity_pool),
        'disclaimer': (
            f"Assessment-based personalization is fully calibrated to your recent mock interview ({questions_answered_meaningfully}/{total_questions_asked} answered, {overall_score_pct}% overall)."
            if has_mock_interview else
            "Baseline plan derived from your resume and target role. Complete a mock interview for adaptive real-time calibration."
        ),
    }
