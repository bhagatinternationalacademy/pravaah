from django import forms
from .models import Skill, TrainerSkill
from trainers.models import Trainer


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['skill_name']


class AssignSkillForm(forms.ModelForm):
    trainer = forms.ModelChoiceField(queryset=Trainer.objects.all())

    class Meta:
        model = TrainerSkill
        fields = ['trainer', 'skill', 'proficiency_level']
        widgets = {
            'proficiency_level': forms.TextInput(attrs={'placeholder': 'e.g., Beginner / Intermediate / Expert'})
        }
