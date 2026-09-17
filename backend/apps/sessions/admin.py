from django.contrib import admin
from .models import InterviewSession, InterviewQuestion, StudentResponse


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'session_type', 'status', 'difficulty', 'created_at')
    list_filter = ('session_type', 'status', 'difficulty')
    search_fields = ('student__user__email',)
    readonly_fields = ('id', 'created_at')


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ('session', 'turn_number', 'phase', 'question_type', 'difficulty_level')
    list_filter = ('phase', 'question_type', 'difficulty_level')
    readonly_fields = ('id', 'created_at')


@admin.register(StudentResponse)
class StudentResponseAdmin(admin.ModelAdmin):
    list_display = ('session', 'score', 'submitted_at')
    readonly_fields = ('id', 'submitted_at')
