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
    question_paragraph = models.TextField(blank=True, null=True)
    question_image = models.ImageField(upload_to='questions/', blank=True, null=True)
    question = models.TextField(default='')
    option_1 = models.CharField(max_length=255, default='')
    option_2 = models.CharField(max_length=255, default='')
    option_3 = models.CharField(max_length=255, default='')
    option_4 = models.CharField(max_length=255, default='')
    correct_answer = models.CharField(
        max_length=20,
        choices=[
            ('option_1', 'Option 1'),
            ('option_2', 'Option 2'),
            ('option_3', 'Option 3'),
            ('option_4', 'Option 4'),
        ],
        default='option_1',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['test_subject__subject', 'sub_title__title', 'level']

    def __str__(self):
        return f'{self.test_subject.subject} / {self.sub_title.title} / {self.get_level_display()}'


class BulkQuestionUpload(models.Model):
    test_subject = models.ForeignKey(TestSubject, on_delete=models.CASCADE, related_name='bulk_uploads')
    sub_title = models.ForeignKey(SubTitle, on_delete=models.CASCADE, related_name='bulk_uploads')
    level = models.CharField(max_length=20, choices=Quiz.LEVEL_CHOICES)
    json_file = models.FileField(upload_to='bulk_questions/', blank=True, null=True)
    questions_json = models.JSONField(
        default=list,
        blank=True,
        help_text='Optional pasted JSON array. Use this only for bulk import data.',
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bulk Question Upload'
        verbose_name_plural = 'Bulk Question Uploads'

    def __str__(self):
        return f'Bulk Upload - {self.test_subject.subject} / {self.sub_title.title} / {self.get_level_display()}'

    def get_level_display(self):
        return dict(Quiz.LEVEL_CHOICES).get(self.level, self.level)
