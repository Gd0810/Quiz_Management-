from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import BulkQuestionUpload, Company, Quiz, SubTitle, TestSubject


class BulkQuestionUploadTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name='Acme',
            email='acme@example.com',
            password='hashed-password',
        )
        self.subject = TestSubject.objects.create(company=self.company, subject='Python')
        self.subtitle = SubTitle.objects.create(test_subject=self.subject, title='Loops')

    def test_import_questions_creates_separate_quiz_rows(self):
        upload = BulkQuestionUpload.objects.create(
            test_subject=self.subject,
            sub_title=self.subtitle,
            level=Quiz.LEVEL_BASIC,
            questions_json=[
                {
                    'question': 'How many loop types are common in Python?',
                    'option_1': '1',
                    'option_2': '2',
                    'option_3': '3',
                    'option_4': '4',
                    'correct_answer': '2',
                },
                {
                    'question': 'Which keyword starts a loop?',
                    'option_1': 'if',
                    'option_2': 'for',
                    'option_3': 'def',
                    'option_4': 'class',
                    'correct_answer': 'for',
                },
            ],
        )

        imported_count = upload.import_questions()

        self.assertEqual(imported_count, 2)
        self.assertEqual(upload.imported_quizzes.count(), 2)
        self.assertEqual(Quiz.objects.filter(bulk_upload=upload).count(), 2)
        self.assertEqual(
            list(upload.imported_quizzes.values_list('correct_answer', flat=True)),
            ['option_2', 'option_2'],
        )

    def test_import_questions_replaces_previous_rows_on_reimport(self):
        upload = BulkQuestionUpload.objects.create(
            test_subject=self.subject,
            sub_title=self.subtitle,
            level=Quiz.LEVEL_BASIC,
            questions_json=[
                {
                    'question': 'Old question',
                    'option_1': 'A',
                    'option_2': 'B',
                    'option_3': 'C',
                    'option_4': 'D',
                    'correct_answer': 'option_1',
                }
            ],
        )
        upload.import_questions()

        upload.questions_json = [
            {
                'question': 'New question',
                'option_1': 'A1',
                'option_2': 'B1',
                'option_3': 'C1',
                'option_4': 'D1',
                'correct_answer': 'option_3',
            }
        ]
        upload.save(update_fields=['questions_json'])

        upload.import_questions()

        self.assertEqual(upload.imported_quizzes.count(), 1)
        self.assertEqual(upload.imported_quizzes.first().question, 'New question')

    def test_import_questions_rejects_missing_required_fields(self):
        upload = BulkQuestionUpload.objects.create(
            test_subject=self.subject,
            sub_title=self.subtitle,
            level=Quiz.LEVEL_BASIC,
            questions_json=[
                {
                    'question': 'Incomplete question',
                    'option_1': 'A',
                    'option_2': '',
                    'option_3': 'C',
                    'option_4': 'D',
                    'correct_answer': 'option_1',
                }
            ],
        )

        with self.assertRaises(ValidationError):
            upload.import_questions()
