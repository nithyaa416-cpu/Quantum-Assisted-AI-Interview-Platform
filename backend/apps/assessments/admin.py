from django.contrib import admin
from .models import CodingSubmission, Assessment, SkillGap


@admin.register(CodingSubmission)
class CodingSubmissionAdmin(admin.ModelAdmin):
    list_display = ('problem_title', 'language', 'overall_score', 'passed_count', 'total_count', 'submitted_at')
    list_filter = ('language', 'timed_out')
    readonly_fields = ('id', 'submitted_at')


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('session', 'overall_score', 'technical_score', 'communication_score', 'generated_at')
    readonly_fields = ('id', 'generated_at')


@admin.register(SkillGap)
class SkillGapAdmin(admin.ModelAdmin):
    list_display = ('skill_name', 'category', 'gap_score', 'priority', 'student', 'identified_at')
    list_filter = ('category', 'priority')
    search_fields = ('skill_name', 'student__user__email')
    readonly_fields = ('id', 'gap_score', 'identified_at')
