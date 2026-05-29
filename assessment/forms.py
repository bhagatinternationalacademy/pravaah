from django import forms
from .models import Assessment


class AssessmentForm(forms.ModelForm):

    class Meta:

        model = Assessment

        fields = [
            'batch',
            'assessment_name',
            'assessment_type',
            'due_date',
            'total_marks',
            'description'
        ]

        widgets = {
            'due_date': forms.DateInput(
                attrs={'type': 'date'}
            )
        }