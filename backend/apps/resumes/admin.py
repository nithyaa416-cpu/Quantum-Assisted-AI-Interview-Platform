"""Admin for resumes app."""
from django.contrib import admin
from django.utils.html import format_html
from .models import Resume, TargetRole


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display  = ('student', 'version', 'is_active', 'parse_status', 'skills_count', 'created_at')
    list_filter   = ('is_active', 'parse_status')
    search_fields = ('student__user__email', 'original_filename')
    readonly_fields = ('id', 'created_at', 'parsed_at', 'parse_status', 'parse_error')

    def skills_count(self, obj):
        return len(obj.parsed_data.get('skills', []))
    skills_count.short_description = 'Skills'

    def parse_status_display(self, obj):
        colors = {'pending': 'orange', 'processing': 'blue', 'completed': 'green', 'failed': 'red'}
        color = colors.get(obj.parse_status, 'grey')
        return format_html(
            '<span style="color:{}; font-weight:bold">{}</span>',
            color, obj.parse_status,
        )
    parse_status_display.short_description = 'Status'


@admin.register(TargetRole)
class TargetRoleAdmin(admin.ModelAdmin):
    list_display  = ('role_name', 'domain', 'student', 'is_primary', 'created_at')
    list_filter   = ('domain', 'is_primary')
    search_fields = ('role_name', 'student__user__email')
