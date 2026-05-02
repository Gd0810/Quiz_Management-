import json

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.hashers import check_password


class Company(models.Model):
    name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='company/', blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    allow_full_screen_lock = models.BooleanField(default=False)
    allow_pause_lock = models.BooleanField(default=False)
    allow_tab_switch_guard = models.BooleanField(default=False)
    full_screen_lock = models.BooleanField(default=False)
    pause_lock = models.BooleanField(default=False)
    tab_switch_guard_enabled = models.BooleanField(default=False)
    max_violation_warnings = models.PositiveIntegerField(default=3)
    exam_control_password = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name

    def check_exam_control_password(self, raw_password):
        if not self.exam_control_password:
            return False
        return check_password(raw_password, self.exam_control_password)


class TestSubject(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subjects')
    subject = models.CharField(max_length=150)
    subject_svg = models.TextField(blank=True, null=True)
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

    bulk_upload = models.ForeignKey(
        'BulkQuestionUpload',
        on_delete=models.SET_NULL,
        related_name='imported_quizzes',
        blank=True,
        null=True,
    )
    test_subject = models.ForeignKey(TestSubject, on_delete=models.CASCADE, related_name='quizzes')
    sub_title = models.ForeignKey(
        SubTitle,
        on_delete=models.SET_NULL,
        related_name='quizzes',
        blank=True,
        null=True,
    )
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
        subtitle_name = self.sub_title.title if self.sub_title else 'General'
        return f'{self.test_subject.subject} / {subtitle_name} / {self.get_level_display()}'


class BulkQuestionUpload(models.Model):
    test_subject = models.ForeignKey(TestSubject, on_delete=models.CASCADE, related_name='bulk_uploads')
    sub_title = models.ForeignKey(
        SubTitle,
        on_delete=models.SET_NULL,
        related_name='bulk_uploads',
        blank=True,
        null=True,
    )
    level = models.CharField(max_length=20, choices=Quiz.LEVEL_CHOICES)
    json_file = models.FileField(upload_to='bulk_questions/', blank=True, null=True)
    questions_json = models.JSONField(
        default=list,
        blank=True,
        help_text='Optional pasted JSON array. Use this only for bulk import data.',
    )
    notes = models.CharField(max_length=255, blank=True)
    imported_count = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bulk Question Upload'
        verbose_name_plural = 'Bulk Question Uploads'

    def __str__(self):
        subtitle_name = self.sub_title.title if self.sub_title else 'General'
        return f'Bulk Upload - {self.test_subject.subject} / {subtitle_name} / {self.get_level_display()}'

    def get_level_display(self):
        return dict(Quiz.LEVEL_CHOICES).get(self.level, self.level)

    def load_questions_payload(self):
        if self.json_file:
            self.json_file.seek(0)
            try:
                return json.loads(self.json_file.read().decode('utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValidationError({'json_file': f'Invalid JSON file: {exc}'}) from exc

        if self.questions_json:
            if isinstance(self.questions_json, list):
                return self.questions_json
            raise ValidationError({'questions_json': 'Bulk JSON must be a list of question objects.'})

        raise ValidationError('Provide either a JSON file or pasted JSON data for bulk import.')

    def _normalize_correct_answer(self, row):
        option_map = {
            'option_1': row.get('option_1', ''),
            'option_2': row.get('option_2', ''),
            'option_3': row.get('option_3', ''),
            'option_4': row.get('option_4', ''),
        }
        raw_answer = str(row.get('correct_answer', '')).strip()
        if raw_answer in option_map:
            return raw_answer

        numeric_map = {
            '1': 'option_1',
            '2': 'option_2',
            '3': 'option_3',
            '4': 'option_4',
        }
        if raw_answer in numeric_map:
            return numeric_map[raw_answer]

        for key, value in option_map.items():
            if raw_answer and raw_answer == str(value).strip():
                return key

        raise ValidationError(
            f'Invalid correct_answer "{raw_answer}" for question "{row.get("question", "")}". '
            'Use option_1..option_4, 1..4, or the exact option text.'
        )

    def import_questions(self):
        payload = self.load_questions_payload()
        if not isinstance(payload, list):
            raise ValidationError('Bulk import data must be a list of question objects.')

        quiz_rows = []
        for index, row in enumerate(payload, start=1):
            if not isinstance(row, dict):
                raise ValidationError(f'Question #{index} must be a JSON object.')

            question_text = str(row.get('question', '')).strip()
            option_1 = str(row.get('option_1', '')).strip()
            option_2 = str(row.get('option_2', '')).strip()
            option_3 = str(row.get('option_3', '')).strip()
            option_4 = str(row.get('option_4', '')).strip()

            if not all([question_text, option_1, option_2, option_3, option_4]):
                raise ValidationError(
                    f'Question #{index} is missing required fields. '
                    'Each row needs question, option_1, option_2, option_3, option_4, and correct_answer.'
                )

            quiz_rows.append(
                Quiz(
                    bulk_upload=self,
                    test_subject=self.test_subject,
                    sub_title=self.sub_title,
                    level=self.level,
                    question_paragraph=row.get('question_paragraph') or row.get('qustionparagraph'),
                    question=question_text,
                    option_1=option_1,
                    option_2=option_2,
                    option_3=option_3,
                    option_4=option_4,
                    correct_answer=self._normalize_correct_answer(row),
                )
            )

        self.imported_quizzes.all().delete()
        Quiz.objects.bulk_create(quiz_rows)
        self.imported_count = len(quiz_rows)

        from django.utils import timezone

        self.processed_at = timezone.now()
        self.save(update_fields=['imported_count', 'processed_at'])
        return self.imported_count
