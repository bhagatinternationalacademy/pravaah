from django import forms

from training_management.form_helpers import ACTIVE_INACTIVE_CHOICES, BootstrapModelForm

from .models import Certification, Trainer, TrainerSkill, ProgramTrainer, CourseTrainer


class TrainerForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=ACTIVE_INACTIVE_CHOICES)

    class Meta:
        model = Trainer
        fields = ["first_name", "last_name", "gender", "dob", "qualification", "mobile", "email", "join_date", "status"]
        widgets = {"dob": forms.DateInput(attrs={"type": "date"}), "join_date": forms.DateInput(attrs={"type": "date"})}


class TrainerSkillForm(BootstrapModelForm):
    class Meta:
        model = TrainerSkill
        fields = ["trainer", "skill_id", "proficiency_level"]


class CertificationForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=ACTIVE_INACTIVE_CHOICES)

    class Meta:
        model = Certification
        fields = ["trainer", "certification_name", "issuing_authority", "certificate_no", "issue_date", "expiry_date", "status"]
        widgets = {"issue_date": forms.DateInput(attrs={"type": "date"}), "expiry_date": forms.DateInput(attrs={"type": "date"})}


class ProgramTrainerForm(BootstrapModelForm):
    class Meta:
        model = ProgramTrainer
        fields = ["trainer", "program", "specialization", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["trainer"].queryset = Trainer.objects.filter(status__iexact="Active", availability__iexact="Available")


class CourseTrainerForm(BootstrapModelForm):
    class Meta:
        model = CourseTrainer
        fields = ["trainer", "course", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["trainer"].queryset = Trainer.objects.filter(status__iexact="Active", availability__iexact="Available")
