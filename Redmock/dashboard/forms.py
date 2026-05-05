from django import forms
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from quiz.models import Candidate, CandidateTestAttempt

from .models import Company, Quiz, SubTitle, TestSubject


class CompanySecurityForm(forms.ModelForm):
    exam_control_password = forms.CharField(
        label='Exam control password',
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text='Leave blank to keep the current exam control password.',
    )
    exam_control_password_confirm = forms.CharField(
        label='Confirm exam control password',
        required=False,
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = Company
        fields = [
            'full_screen_lock',
            'pause_lock',
            'tab_switch_guard_enabled',
            'copy_paste_block_enabled',
            'right_click_disable_enabled',
            'max_violation_warnings',
            'exam_control_password',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        gated_fields = {
            'full_screen_lock': self.instance.allow_full_screen_lock,
            'pause_lock': self.instance.allow_pause_lock,
            'tab_switch_guard_enabled': self.instance.allow_tab_switch_guard,
            'copy_paste_block_enabled': self.instance.allow_copy_paste_block,
            'right_click_disable_enabled': self.instance.allow_right_click_disable,
        }
        for field_name, is_allowed in gated_fields.items():
            if is_allowed:
                continue
            self.fields.pop(field_name, None)

        if not self.instance.allow_tab_switch_guard:
            self.fields.pop('max_violation_warnings', None)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('exam_control_password', '').strip()
        confirm = cleaned_data.get('exam_control_password_confirm', '').strip()

        if password or confirm:
            if password != confirm:
                raise ValidationError('Exam control password and confirm password must match.')
            cleaned_data['exam_control_password'] = make_password(password)
        else:
            cleaned_data['exam_control_password'] = self.instance.exam_control_password

        if not self.instance.allow_full_screen_lock:
            cleaned_data['full_screen_lock'] = False
        if not self.instance.allow_pause_lock:
            cleaned_data['pause_lock'] = False
        if not self.instance.allow_tab_switch_guard:
            cleaned_data['tab_switch_guard_enabled'] = False
            cleaned_data['max_violation_warnings'] = self.instance.max_violation_warnings
        if not self.instance.allow_copy_paste_block:
            cleaned_data['copy_paste_block_enabled'] = False
        if not self.instance.allow_right_click_disable:
            cleaned_data['right_click_disable_enabled'] = False

        if (cleaned_data.get('full_screen_lock') or cleaned_data.get('pause_lock')) and not cleaned_data.get('exam_control_password'):
            raise ValidationError('Set an exam control password before enabling fullscreen lock or pause lock.')

        if cleaned_data.get('tab_switch_guard_enabled') and cleaned_data.get('max_violation_warnings', 0) <= 0:
            raise ValidationError('Maximum violation warnings must be greater than zero when tab switch guard is enabled.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.allow_full_screen_lock:
            instance.full_screen_lock = False
        if not instance.allow_pause_lock:
            instance.pause_lock = False
        if not instance.allow_tab_switch_guard:
            instance.tab_switch_guard_enabled = False
        if not instance.allow_copy_paste_block:
            instance.copy_paste_block_enabled = False
        if not instance.allow_right_click_disable:
            instance.right_click_disable_enabled = False
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class CompanyInstructionsForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['test_instructions']
        labels = {
            'test_instructions': 'Online test instructions',
        }
        widgets = {
            'test_instructions': forms.Textarea(
                attrs={
                    'rows': 10,
                    'data-tinymce': 'true',
                }
            ),
        }


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
            'full_screen_lock_enabled',
            'pause_lock_enabled',
            'tab_switch_guard_enabled',
            'copy_paste_block_enabled',
            'right_click_disable_enabled',
            'max_violation_warnings',
        ]
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'submitted_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
