from django.db import models

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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.candidate.name} - {self.company.name} ({self.session_type})'
