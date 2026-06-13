from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from dashboard.models import Company

from .models import Candidate, CandidateTestAttempt


class TestLinkEmailTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name='Redback',
            email='admin@example.com',
            password='hashed-password',
        )
        self.candidate = Candidate.objects.create(
            name='Kiran',
            email='kiran@example.com',
            designation_tech='Developer',
        )
        self.attempt = CandidateTestAttempt.objects.create(
            candidate=self.candidate,
            company=self.company,
            session_type=CandidateTestAttempt.SESSION_SINGLE,
            level='basic',
            question_count=1,
            duration_minutes=30,
        )

    def test_send_test_link_email_skips_when_mail_disabled(self):
        response = self.client.post(reverse('quiz:send_test_link_email', args=[self.attempt.public_slug]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'skipped')

    def test_send_test_link_email_sends_once_when_mail_ready(self):
        self.company.mail_sender_enabled = True
        self.company.smtp_host = 'smtp.example.com'
        self.company.smtp_port = 587
        self.company.smtp_username = 'sender@example.com'
        self.company.smtp_app_key = 'app-key'
        self.company.save()

        with patch('quiz.views.EmailMessage.send', return_value=1) as mocked_send:
            response = self.client.post(reverse('quiz:send_test_link_email', args=[self.attempt.public_slug]))
            second_response = self.client.post(reverse('quiz:send_test_link_email', args=[self.attempt.public_slug]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'sent')
        self.assertEqual(second_response.json()['status'], 'already_sent')
        self.assertEqual(mocked_send.call_count, 1)
        self.attempt.refresh_from_db()
        self.assertIsNotNone(self.attempt.test_link_email_sent_at)
