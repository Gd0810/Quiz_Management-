from django import forms
from django.core.exceptions import ValidationError

from quiz.models import Candidate, CandidateTestAttempt

from .models import Quiz, SubTitle, TestSubject


class TestSubjectForm(forms.ModelForm):
    class Meta:
        model = TestSubject
        fields = ['subject']


class SubTitleForm(forms.ModelForm):
    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            self.fields['test_subject'].queryset = TestSubject.objects.filter(company=company)

    class Meta:
        model = SubTitle
        fields = ['test_subject', 'title']


class QuizForm(forms.ModelForm):
    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_title'].required = False
        if company is not None:
            subject_queryset = TestSubject.objects.filter(company=company)
            self.fields['test_subject'].queryset = subject_queryset
            self.fields['sub_title'].queryset = SubTitle.objects.filter(test_subject__company=company)

    def clean(self):
        cleaned_data = super().clean()
        test_subject = cleaned_data.get('test_subject')
        sub_title = cleaned_data.get('sub_title')
        if test_subject and sub_title and sub_title.test_subject_id != test_subject.id:
            raise ValidationError('Selected sub title does not belong to the selected test subject.')
        return cleaned_data

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
    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            self.fields['company'].queryset = self.fields['company'].queryset.filter(id=company.id)
            self.fields['company'].initial = company

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
