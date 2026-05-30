from django import forms

from training_management.form_helpers import ACTIVE_INACTIVE_CHOICES, BootstrapModelForm

from .models import Student, StudentGuardian


class StudentForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=ACTIVE_INACTIVE_CHOICES)

    class Meta:
        model = Student
        fields = ["student_code", "first_name", "last_name", "course", "gender", "dob", "mobile", "email", "join_date", "status"]
        labels = {"student_code": "Admission No"}
        widgets = {"dob": forms.DateInput(attrs={"type": "date"}), "join_date": forms.DateInput(attrs={"type": "date"})}


class StudentGuardianForm(BootstrapModelForm):
    class Meta:
        model = StudentGuardian
        fields = ["student", "guardian_name", "relation", "mobile", "email", "occupation"]
        labels = {"relation": "Relationship", "occupation": "Address"}
