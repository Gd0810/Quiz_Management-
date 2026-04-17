from django import forms

from dashboard.models import Quiz, SubTitle, TestSubject


class CandidateStartForm(forms.Form):
    SESSION_CHOICES = [
        ('single', 'Single'),
        ('multi', 'Multi'),
    ]

    candidate_name = forms.CharField(max_length=150)
    candidate_email = forms.EmailField()
    designation_tech = forms.CharField(max_length=150)
    session_type = forms.ChoiceField(choices=SESSION_CHOICES, initial='single')
    level = forms.ChoiceField(choices=Quiz.LEVEL_CHOICES)
    duration_minutes = forms.IntegerField(min_value=1, initial=30)
    question_count = forms.IntegerField(min_value=1, initial=10)
    subjects = forms.ModelMultipleChoiceField(
        queryset=TestSubject.objects.select_related('company').all(),
        widget=forms.CheckboxSelectMultiple,
    )
    sub_titles = forms.ModelMultipleChoiceField(
        queryset=SubTitle.objects.select_related('test_subject').all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def clean(self):
        cleaned_data = super().clean()
        session_type = cleaned_data.get('session_type')
        subjects = cleaned_data.get('subjects')
        sub_titles = cleaned_data.get('sub_titles')

        if session_type == 'single' and subjects and len(subjects) != 1:
            self.add_error('subjects', 'Single session test must have exactly one subject.')

        if session_type == 'multi' and subjects and len(subjects) < 2:
            self.add_error('subjects', 'Multi session test must have at least two subjects.')

        if subjects and sub_titles:
            invalid_subtitles = [
                subtitle.title
                for subtitle in sub_titles
                if subtitle.test_subject_id not in {subject.id for subject in subjects}
            ]
            if invalid_subtitles:
                self.add_error(
                    'sub_titles',
                    f'Selected sub titles do not match chosen subjects: {", ".join(invalid_subtitles)}',
                )

        return cleaned_data
