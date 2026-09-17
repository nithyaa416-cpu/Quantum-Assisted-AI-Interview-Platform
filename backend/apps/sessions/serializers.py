"""Serializers for sessions app."""
from rest_framework import serializers
from .models import InterviewSession, InterviewQuestion, StudentResponse


class InterviewSessionSerializer(serializers.ModelSerializer):
    target_role_name = serializers.CharField(
        source='target_role.role_name', read_only=True, default=None
    )
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSession
        fields = [
            'id', 'session_type', 'status', 'difficulty',
            'target_role', 'target_role_name',
            'quantum_plan', 'started_at', 'ended_at',
            'duration_seconds', 'notes', 'question_count', 'created_at',
        ]
        read_only_fields = [
            'id', 'status', 'started_at', 'ended_at',
            'duration_seconds', 'question_count', 'created_at',
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = [
            'id', 'session', 'turn_number', 'phase',
            'question_text', 'question_type', 'topic',
            'difficulty_level', 'expected_concepts',
            'ai_generated', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class StudentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentResponse
        fields = [
            'id', 'question', 'session', 'transcript',
            'audio_file', 'response_duration_seconds',
            'concepts_covered', 'score', 'ai_feedback', 'submitted_at',
        ]
        read_only_fields = ['id', 'score', 'ai_feedback', 'submitted_at']
