from django import forms
from .models import Certification


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['trainer', 'certification_name', 'issuing_organization', 'issue_date', 'expiry_date', 'certificate_file']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
