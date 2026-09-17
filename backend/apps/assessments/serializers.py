"""Serializers for assessments app."""
from rest_framework import serializers
from .models import CodingSubmission, Assessment, SkillGap


class CodingSubmissionSerializer(serializers.ModelSerializer):
    pass_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = CodingSubmission
        fields = [
            'id', 'session', 'problem_title', 'problem_statement',
            'language', 'code', 'execution_output', 'stderr',
            'test_results', 'passed_count', 'total_count',
            'runtime_ms', 'memory_kb', 'timed_out',
            'correctness_score', 'efficiency_score', 'quality_score',
            'overall_score', 'llm_review', 'pass_rate', 'submitted_at',
        ]
        read_only_fields = [
            'id', 'execution_output', 'stderr', 'test_results',
            'passed_count', 'total_count', 'runtime_ms', 'memory_kb',
            'timed_out', 'correctness_score', 'efficiency_score',
            'quality_score', 'overall_score', 'llm_review',
            'pass_rate', 'submitted_at',
        ]


class AssessmentSerializer(serializers.ModelSerializer):
    session_type = serializers.CharField(source='session.session_type', read_only=True)
    target_role = serializers.CharField(
        source='session.target_role.role_name', read_only=True, default=None
    )

    class Meta:
        model = Assessment
        fields = [
            'id', 'session', 'session_type', 'target_role',
            'overall_score', 'technical_score', 'communication_score',
            'behavioural_score', 'coding_score', 'problem_solving_score',
            'strengths', 'improvement_areas', 'detailed_feedback',
            'speech_metrics', 'behavioural_metrics', 'generated_at',
        ]
        read_only_fields = fields


class SkillGapSerializer(serializers.ModelSerializer):
    is_resolved = serializers.BooleanField(read_only=True)

    class Meta:
        model = SkillGap
        fields = [
            'id', 'skill_name', 'category',
            'current_level', 'target_level', 'gap_score',
            'priority', 'identified_at', 'resolved_at', 'is_resolved',
        ]
        read_only_fields = ['id', 'gap_score', 'priority', 'identified_at', 'is_resolved']
