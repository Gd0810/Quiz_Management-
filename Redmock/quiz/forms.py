from django import forms


class CandidateDetailsForm(forms.Form):
    candidate_name = forms.CharField(max_length=150)
    candidate_email = forms.EmailField()
    designation_tech = forms.CharField(max_length=150)
