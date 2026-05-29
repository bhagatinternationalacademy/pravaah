from django import forms

from training_management.form_helpers import ASSESSMENT_RESULT_STATUS_CHOICES, BootstrapModelForm

from .models import Assessment, AssessmentResult


class AssessmentForm(BootstrapModelForm):
    class Meta:
        model = Assessment
        fields = ["course", "assessment_name", "assessment_type", "total_marks", "passing_marks", "instructions"]


class AssessmentResultForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=ASSESSMENT_RESULT_STATUS_CHOICES)

    class Meta:
        model = AssessmentResult
        fields = ["enrollment", "assessment", "marks_obtained", "status", "submitted_at", "graded_at"]
        widgets = {
            "submitted_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "graded_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
