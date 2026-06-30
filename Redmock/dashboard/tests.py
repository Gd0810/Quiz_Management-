import json

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

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


class SubjectQuestionUploadViewTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name='Acme',
            email='acme@example.com',
            password='hashed-password',
        )
        self.subject = TestSubject.objects.create(company=self.company, subject='Python')
        session = self.client.session
        session['company_id'] = self.company.id
        session.save()

    def test_upload_questions_without_subtitles_imports_as_general(self):
        payload = [
            {
                'question_paragraph': 'Python has built-in data types.',
                'question': 'What is type(10.5)?',
                'option_1': "<class 'int'>",
                'option_2': "<class 'float'>",
                'option_3': "<class 'number'>",
                'option_4': "<class 'decimal'>",
                'correct_answer': 'option_2',
            }
        ]

        response = self.client.post(
            reverse('dashboard:subject_question_upload'),
            {
                'test_subject': self.subject.id,
                'sub_title': '',
                'level': Quiz.LEVEL_BASIC,
                'questions_text': json.dumps(payload),
                'notes': 'Python data types',
            },
        )

        self.assertRedirects(response, reverse('dashboard:subject_list'))
        quiz = Quiz.objects.get(test_subject=self.subject)
        self.assertIsNone(quiz.sub_title)
        self.assertEqual(quiz.question, 'What is type(10.5)?')
        self.assertEqual(quiz.correct_answer, 'option_2')


class AttemptListViewAndPDFTests(TestCase):
    def setUp(self):
        from quiz.models import Candidate, CandidateTestAttempt
        self.company = Company.objects.create(
            name='Acme Corp',
            email='acme@example.com',
            password='hashed-password',
        )
        session = self.client.session
        session['company_id'] = self.company.id
        session.save()

        # Create candidates
        self.candidate1 = Candidate.objects.create(name='Alice Smith', email='alice@example.com')
        self.candidate2 = Candidate.objects.create(name='Bob Jones', email='bob@example.com')

        # Create test attempts
        self.attempt1 = CandidateTestAttempt.objects.create(
            candidate=self.candidate1,
            company=self.company,
            session_type='single',
            level='basic',
            question_count=10,
            duration_minutes=30,
            percentage=80.00
        )
        self.attempt2 = CandidateTestAttempt.objects.create(
            candidate=self.candidate2,
            company=self.company,
            session_type='single',
            level='experienced',
            question_count=10,
            duration_minutes=30,
            percentage=45.00
        )

    def test_attempt_list_filter_search(self):
        # Search by candidate name 'Alice'
        url = reverse('dashboard:attempt_list')
        response = self.client.get(url, {'q': 'Alice'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Smith')
        self.assertNotContains(response, 'Bob Jones')

        # Search by email domain
        response = self.client.get(url, {'q': 'bob@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bob Jones')
        self.assertNotContains(response, 'Alice Smith')

    def test_attempt_list_filter_level(self):
        url = reverse('dashboard:attempt_list')
        # Filter basic level
        response = self.client.get(url, {'level': 'basic'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Smith')
        self.assertNotContains(response, 'Bob Jones')

        # Filter experienced level
        response = self.client.get(url, {'level': 'experienced'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bob Jones')
        self.assertNotContains(response, 'Alice Smith')

    def test_attempt_list_filter_percentage(self):
        url = reverse('dashboard:attempt_list')
        # Filter minimum percentage 50% (alice 80% should be shown, bob 45% should not)
        response = self.client.get(url, {'percentage': '50'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Smith')
        self.assertNotContains(response, 'Bob Jones')

        # Filter minimum percentage 40% (both should show)
        response = self.client.get(url, {'percentage': '40'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Smith')
        self.assertContains(response, 'Bob Jones')

    def test_attempt_pdf_download(self):
        url = reverse('dashboard:attempt_pdf')
        # Request full list as PDF
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.has_header('Content-Disposition'))
        self.assertIn('attachment;', response['Content-Disposition'])

        # Request filtered list as PDF (search for Bob only)
        response = self.client.get(url, {'q': 'Bob'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

