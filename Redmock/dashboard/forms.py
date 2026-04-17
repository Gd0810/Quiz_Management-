from django import forms

from quiz.models import Candidate, CandidateTestAttempt

from .models import Quiz, SubTitle, TestSubject


class TestSubjectForm(forms.ModelForm):
    class Meta:
        model = TestSubject
        fields = ['company', 'subject']


class SubTitleForm(forms.ModelForm):
    class Meta:
        model = SubTitle
        fields = ['test_subject', 'title']


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'test_subject',
            'sub_title',
            'level',
            'question_paragraph',
            'question_image',
            'question',
            'option_1',
            'option_2',
            'option_3',
            'option_4',
            'correct_answer',
        ]
        widgets = {
            'question_paragraph': forms.Textarea(attrs={'rows': 3}),
            'question': forms.Textarea(attrs={'rows': 3}),
        }


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'email', 'designation_tech']


class CandidateTestAttemptForm(forms.ModelForm):
    class Meta:
        model = CandidateTestAttempt
        fields = [
            'candidate',
            'company',
            'session_type',
            'level',
            'question_count',
            'duration_minutes',
            'selected_subjects',
            'selected_sub_titles',
            'answers_json',
            'correct_count',
            'wrong_count',
            'percentage',
            'started_at',
            'submitted_at',
            'is_submitted',
        ]
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'submitted_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
