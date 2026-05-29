from django import forms

from training_management.form_helpers import CERTIFICATE_STATUS_CHOICES, BootstrapModelForm

from .models import Certificate


class CertificateForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=CERTIFICATE_STATUS_CHOICES)

    class Meta:
        model = Certificate
        fields = ["enrollment", "certificate_no", "issue_date", "expiry_date", "certificate_url", "verification_code", "status"]
        widgets = {"issue_date": forms.DateInput(attrs={"type": "date"}), "expiry_date": forms.DateInput(attrs={"type": "date"})}
