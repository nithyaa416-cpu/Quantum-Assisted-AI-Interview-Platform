"""Serializers for preparation app."""
from rest_framework import serializers
from .models import PreparationPlan, PracticeModule


class PracticeModuleSerializer(serializers.ModelSerializer):
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = PracticeModule
        fields = [
            'id', 'topic', 'sub_topics', 'scheduled_day',
            'estimated_hours', 'status', 'completed_at',
            'resources', 'is_completed', 'created_at',
        ]
        read_only_fields = ['id', 'is_completed', 'created_at']


class PreparationPlanSerializer(serializers.ModelSerializer):
    target_role_name = serializers.CharField(
        source='target_role.role_name', read_only=True, default=None
    )
    modules_count = serializers.SerializerMethodField()
    completed_modules = serializers.SerializerMethodField()

    class Meta:
        model = PreparationPlan
        fields = [
            'id', 'target_role', 'target_role_name',
            'preparation_days', 'topic_weights', 'recommended_sequence',
            'qaoa_energy', 'circuit_depth', 'is_active',
            'modules_count', 'completed_modules',
            'generated_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'topic_weights', 'recommended_sequence',
            'qaoa_energy', 'circuit_depth', 'generated_at', 'updated_at',
        ]

    def get_modules_count(self, obj):
        return obj.practice_modules.count()

    def get_completed_modules(self, obj):
        return obj.practice_modules.filter(status='completed').count()
