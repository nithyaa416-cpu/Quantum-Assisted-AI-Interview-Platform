"""
Serializers for the Coding Interview module.

Key security rule implemented here:
  - CodingTestCasePublicSerializer NEVER returns is_hidden, input_data,
    or expected_output for hidden test cases.
  - The frontend only ever receives public test case input/expected for
    the sample display — never hidden ones.
"""
from rest_framework import serializers
from .models import CodingProblem, CodingTestCase, CodingSubmission


class CodingTestCasePublicSerializer(serializers.ModelSerializer):
    """
    Safe serializer for PUBLIC test cases only.
    Returns input + expected output so students can see examples.
    NEVER use this for hidden test cases.
    """
    class Meta:
        model  = CodingTestCase
        fields = ['id', 'input_data', 'expected_output', 'order']


class CodingProblemListSerializer(serializers.ModelSerializer):
    """Lightweight serialiser for the problem list endpoint."""
    class Meta:
        model  = CodingProblem
        fields = [
            'id', 'title', 'slug', 'difficulty',
            'time_limit_seconds', 'memory_limit_mb',
        ]


class CodingProblemDetailSerializer(serializers.ModelSerializer):
    """
    Full problem detail including visible test cases.
    Hidden test cases are EXCLUDED — they are only used server-side.
    """
    public_test_cases = serializers.SerializerMethodField()

    class Meta:
        model  = CodingProblem
        fields = [
            'id', 'title', 'slug', 'difficulty',
            'description', 'input_format', 'output_format',
            'constraints', 'examples', 'starter_code',
            'time_limit_seconds', 'memory_limit_mb',
            'public_test_cases',
        ]

    def get_public_test_cases(self, obj):
        # Return only is_hidden=False test cases
        qs = obj.test_cases.filter(is_hidden=False).order_by('order')
        return CodingTestCasePublicSerializer(qs, many=True).data


class RunResultSerializer(serializers.Serializer):
    """Result for a single test case execution (Run Code response)."""
    test_case_id = serializers.CharField()
    status       = serializers.CharField()
    stdout       = serializers.CharField(allow_blank=True)
    stderr       = serializers.CharField(allow_blank=True)
    time_ms      = serializers.FloatField(allow_null=True)
    memory_kb    = serializers.IntegerField(allow_null=True)
    passed       = serializers.BooleanField()


class CodingRunResponseSerializer(serializers.Serializer):
    """Full Run Code response envelope."""
    overall_status = serializers.CharField()
    passed         = serializers.IntegerField()
    total          = serializers.IntegerField()
    runtime_ms     = serializers.FloatField(allow_null=True)
    memory_kb      = serializers.IntegerField(allow_null=True)
    results        = RunResultSerializer(many=True)


class CodingSubmissionSafeSerializer(serializers.ModelSerializer):
    """
    Safe read serialiser for a stored submission.
    Does NOT return hidden test case details or expected outputs.
    """
    pass_rate = serializers.FloatField(read_only=True)
    # Safe test_results: strip expected_output for hidden cases
    safe_results = serializers.SerializerMethodField()

    class Meta:
        model  = CodingSubmission
        fields = [
            'id', 'problem_title', 'language', 'status',
            'passed_count', 'total_count', 'runtime_ms', 'memory_kb',
            'correctness_score', 'overall_score', 'pass_rate',
            'safe_results', 'submitted_at',
        ]
        read_only_fields = fields

    def get_safe_results(self, obj):
        """Strip expected_output from results (already not stored for hidden cases)."""
        safe = []
        for r in (obj.test_results or []):
            safe.append({
                'test_case_id': r.get('test_case_id', ''),
                'status':       r.get('status', ''),
                'stdout':       r.get('stdout', ''),
                'passed':       r.get('passed', False),
                'time_ms':      r.get('time_ms'),
                'memory_kb':    r.get('memory_kb'),
                # Never return expected_output or hidden input here
            })
        return safe
