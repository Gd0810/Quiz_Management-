from django.contrib import admin

from .models import Candidate, CandidateTestAttempt


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'designation_tech', 'created_at')
    search_fields = ('name', 'email', 'designation_tech')


@admin.register(CandidateTestAttempt)
class CandidateTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'candidate',
        'company',
        'session_type',
        'level',
        'question_count',
        'tab_switch_count',
        'warning_count',
        'correct_count',
        'wrong_count',
        'percentage',
        'is_submitted',
        'created_at',
    )
    list_filter = ('session_type', 'level', 'is_submitted', 'company')
    search_fields = ('candidate__name', 'candidate__email', 'company__name')
