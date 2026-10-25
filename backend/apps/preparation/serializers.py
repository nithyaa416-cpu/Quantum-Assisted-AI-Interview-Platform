"""
Serializers for QAOA-based preparation plans, practice modules, and feedback analysis.
"""
from rest_framework import serializers
from .models import PreparationPlan, PracticeModule
from apps.resumes.models import TargetRole
from apps.sessions.models import InterviewSession


class PracticeModuleSerializer(serializers.ModelSerializer):
    is_completed = serializers.BooleanField(read_only=True)
    estimated_hours = serializers.FloatField()

    class Meta:
        model = PracticeModule
        fields = [
            'id', 'plan', 'activity_id', 'topic', 'sub_topics', 'scheduled_day',
            'estimated_hours', 'priority', 'why_selected', 'expected_outcome',
            'practice_exercises', 'prerequisites', 'order', 'status',
            'completed_at', 'resources', 'is_completed', 'created_at',
        ]
        read_only_fields = ['id', 'is_completed', 'created_at']


class PreparationPlanSerializer(serializers.ModelSerializer):
    target_role_name = serializers.CharField(
        source='target_role.role_name', read_only=True, default=None
    )
    session_id = serializers.UUIDField(
        source='session.id', read_only=True, default=None
    )
    modules_count = serializers.SerializerMethodField()
    completed_modules = serializers.SerializerMethodField()
    practice_modules = PracticeModuleSerializer(many=True, read_only=True)

    class Meta:
        model = PreparationPlan
        fields = [
            'id', 'target_role', 'target_role_name', 'session', 'session_id',
            'preparation_days', 'total_hours_budget', 'daily_hours',
            'algorithm_used', 'topic_weights', 'recommended_sequence',
            'feedback_summary', 'priority_areas', 'optimization_metadata',
            'qaoa_energy', 'circuit_depth', 'is_active',
            'modules_count', 'completed_modules', 'practice_modules',
            'generated_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'topic_weights', 'recommended_sequence', 'feedback_summary',
            'optimization_metadata', 'qaoa_energy', 'circuit_depth',
            'generated_at', 'updated_at',
        ]

    def get_modules_count(self, obj):
        return obj.practice_modules.count()

    def get_completed_modules(self, obj):
        return obj.practice_modules.filter(status='completed').count()


class GeneratePlanRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False, allow_null=True)
    target_role_id = serializers.UUIDField(required=False, allow_null=True)
    days_remaining = serializers.IntegerField(required=False, default=7, min_value=1, max_value=60)
    daily_hours = serializers.FloatField(required=False, default=2.0, min_value=0.5, max_value=12.0)
    total_hours_budget = serializers.FloatField(required=False, allow_null=True, min_value=1.0, max_value=200.0)
    priority_areas = serializers.ListField(
        child=serializers.CharField(max_length=100), required=False, default=list
    )
    preferred_categories = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, default=list
    )
    force_algorithm = serializers.ChoiceField(
        choices=['qaoa', 'classical'], required=False, default='qaoa'
    )


class ModuleStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['pending', 'in_progress', 'completed', 'skipped'])


class BenchmarkRequestSerializer(serializers.Serializer):
    num_qubits = serializers.IntegerField(required=False, default=6, min_value=3, max_value=10)
    total_hours_budget = serializers.FloatField(required=False, default=12.0, min_value=2.0, max_value=40.0)
    p_layers = serializers.IntegerField(required=False, default=1, min_value=1, max_value=2)
