from django.db import models
from django.utils import timezone

from dashboard.models import Company


class Candidate(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    designation_tech = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.email})'


class CandidateTestAttempt(models.Model):
    SESSION_SINGLE = 'single'
    SESSION_MULTI = 'multi'
    SESSION_CHOICES = [
        (SESSION_SINGLE, 'Single'),
        (SESSION_MULTI, 'Multi'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='attempts')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='attempts')
    session_type = models.CharField(max_length=10, choices=SESSION_CHOICES)
    level = models.CharField(max_length=20)
    question_count = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField()
    selected_subjects = models.JSONField(default=list, blank=True)
    selected_sub_titles = models.JSONField(default=list, blank=True)
    answers_json = models.JSONField(default=list, blank=True)
    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    started_at = models.DateTimeField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    is_submitted = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)
    paused_at = models.DateTimeField(blank=True, null=True)
    total_paused_seconds = models.PositiveIntegerField(default=0)
    tab_switch_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    last_violation_at = models.DateTimeField(blank=True, null=True)
    violation_log_json = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.candidate.name} - {self.company.name} ({self.session_type})'

    def current_pause_seconds(self, now=None):
        if not self.is_paused or not self.paused_at:
            return 0
        now = now or timezone.now()
        return max(int((now - self.paused_at).total_seconds()), 0)

    def remaining_seconds(self, now=None):
        if not self.started_at:
            return 0
        now = now or timezone.now()
        elapsed_seconds = int((now - self.started_at).total_seconds())
        consumed_seconds = max(
            elapsed_seconds - self.total_paused_seconds - self.current_pause_seconds(now),
            0,
        )
        return max((self.duration_minutes * 60) - consumed_seconds, 0)
