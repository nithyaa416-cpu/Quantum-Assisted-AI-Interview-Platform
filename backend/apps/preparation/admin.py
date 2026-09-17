from django.contrib import admin
from .models import PreparationPlan, PracticeModule


@admin.register(PreparationPlan)
class PreparationPlanAdmin(admin.ModelAdmin):
    list_display = ('student', 'target_role', 'preparation_days', 'is_active', 'generated_at')
    list_filter = ('is_active',)
    search_fields = ('student__user__email',)
    readonly_fields = ('id', 'generated_at', 'updated_at')


@admin.register(PracticeModule)
class PracticeModuleAdmin(admin.ModelAdmin):
    list_display = ('topic', 'student', 'scheduled_day', 'estimated_hours', 'status')
    list_filter = ('status',)
    search_fields = ('topic', 'student__user__email')
    readonly_fields = ('id', 'created_at')
