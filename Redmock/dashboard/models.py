from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='company/', blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


class TestSubject(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subjects')
    subject = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subject']
        unique_together = ('company', 'subject')

    def __str__(self):
        return f'{self.company.name} - {self.subject}'


class SubTitle(models.Model):
    test_subject = models.ForeignKey(TestSubject, on_delete=models.CASCADE, related_name='sub_titles')
    title = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        unique_together = ('test_subject', 'title')

    def __str__(self):
        return f'{self.test_subject.subject} - {self.title}'


class Quiz(models.Model):
    LEVEL_BASIC = 'basic'
    LEVEL_INTERMEDIATE = 'intermediate'
    LEVEL_EXPERIENCED = 'experienced'
    LEVEL_CHOICES = [
        (LEVEL_BASIC, 'Basic'),
        (LEVEL_INTERMEDIATE, 'Intermediate'),
        (LEVEL_EXPERIENCED, 'Experienced'),
    ]

    test_subject = models.ForeignKey(TestSubject, on_delete=models.CASCADE, related_name='quizzes')
    sub_title = models.ForeignKey(SubTitle, on_delete=models.CASCADE, related_name='quizzes')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    questions_json = models.JSONField(default=list, help_text='Bulk-uploaded question bank as a JSON array.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['test_subject__subject', 'sub_title__title', 'level']

    def __str__(self):
        return f'{self.test_subject.subject} / {self.sub_title.title} / {self.get_level_display()}'
