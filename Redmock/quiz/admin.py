from django.contrib import admin
from django.utils.html import format_html_join

from .models import Candidate, CandidateTestAttempt


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'designation_tech', 'candidate_details_summary', 'created_at')
    readonly_fields = ('candidate_details_summary',)
    search_fields = ('name', 'email', 'designation_tech')


@admin.register(CandidateTestAttempt)
class CandidateTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'candidate',
        'company',
        'public_slug',
        'session_type',
        'level',
        'question_count',
        'candidate_details_preview',
        'full_screen_lock_enabled',
        'pause_lock_enabled',
        'tab_switch_guard_enabled',
        'copy_paste_block_enabled',
        'right_click_disable_enabled',
        'max_violation_warnings',
        'tab_switch_count',
        'warning_count',
        'correct_count',
        'wrong_count',
        'percentage',
        'is_submitted',
        'created_at',
    )
    list_filter = (
        'session_type',
        'level',
        'full_screen_lock_enabled',
        'pause_lock_enabled',
        'tab_switch_guard_enabled',
        'copy_paste_block_enabled',
        'right_click_disable_enabled',
        'is_submitted',
        'company',
    )
    search_fields = ('candidate__name', 'candidate__email', 'company__name', 'public_slug')
    readonly_fields = ('candidate_details_json',)

    def candidate_details_preview(self, obj):
        values = (obj.candidate_details_json or {}).get('values') or {}
        labels = (obj.candidate_details_json or {}).get('labels') or {}
        if not values:
            return '-'
        return format_html_join(
            '',
            '{}: {}<br>',
            ((labels.get(key, key), value) for key, value in values.items()),
        )

    candidate_details_preview.short_description = 'Candidate Details'
