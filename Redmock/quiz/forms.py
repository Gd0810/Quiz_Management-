from django import forms

from dashboard.models import CandidateFormField


class CandidateDetailsForm(forms.Form):
    candidate_name = forms.CharField(max_length=150, label='Name')
    candidate_email = forms.EmailField(label='Email')

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['candidate_name'].widget.attrs.update({'placeholder': 'Enter your full name'})
        self.fields['candidate_email'].widget.attrs.update({'placeholder': 'Enter your email address'})
        self.custom_fields = []
        if company is None:
            return

        fields = company.candidate_form_fields.filter(is_active=True).order_by('sort_order', 'label')
        for form_field in fields:
            field_name = f'custom_{form_field.field_key}'
            self.fields[field_name] = self._build_field(form_field)
            self.custom_fields.append((field_name, form_field))

    def _base_attrs(self, form_field):
        attrs = {}
        if form_field.placeholder:
            attrs['placeholder'] = form_field.placeholder
        return attrs

    def _build_field(self, form_field):
        attrs = self._base_attrs(form_field)
        kwargs = {
            'label': form_field.label,
            'required': form_field.required,
            'help_text': form_field.help_text,
        }

        if form_field.field_type == CandidateFormField.FIELD_EMAIL:
            return forms.EmailField(widget=forms.EmailInput(attrs=attrs), **kwargs)
        if form_field.field_type == CandidateFormField.FIELD_PHONE:
            attrs['type'] = 'tel'
            return forms.CharField(max_length=40, widget=forms.TextInput(attrs=attrs), **kwargs)
        if form_field.field_type == CandidateFormField.FIELD_NUMBER:
            return forms.DecimalField(widget=forms.NumberInput(attrs=attrs), **kwargs)
        if form_field.field_type == CandidateFormField.FIELD_TEXTAREA:
            return forms.CharField(widget=forms.Textarea(attrs={**attrs, 'rows': 3}), **kwargs)
        if form_field.field_type == CandidateFormField.FIELD_DATE:
            return forms.DateField(widget=forms.DateInput(attrs={**attrs, 'type': 'date'}), **kwargs)
        return forms.CharField(max_length=150, widget=forms.TextInput(attrs=attrs), **kwargs)

    def custom_details(self):
        details = {}
        labels = {}
        for field_name, form_field in self.custom_fields:
            value = self.cleaned_data.get(field_name)
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            elif value is not None and not isinstance(value, (bool, int, float, str, list, dict)):
                value = str(value)
            details[form_field.field_key] = value
            labels[form_field.field_key] = form_field.label
        return {'values': details, 'labels': labels}
