from django import forms
from .models import Trainer


class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['trainer_code', 'first_name', 'last_name', 'qualification', 'specialization', 'mobile', 'email', 'joining_date', 'status', 'profile_photo', 'availability']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(choices=[('Active','Active'),('Inactive','Inactive')]),
            'availability': forms.Select(choices=[('Available','Available'),('Busy','Busy'),('On Leave','On Leave')]),
        }

    def clean_trainer_code(self):
        code = self.cleaned_data.get('trainer_code')
        return code.strip()


class TrainerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['trainer_code', 'first_name', 'last_name', 'qualification', 'specialization', 'mobile', 'email', 'profile_photo']

    def clean_trainer_code(self):
        code = self.cleaned_data.get('trainer_code')
        return code.strip()


class TrainerProfileEditForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['mobile', 'email', 'availability', 'profile_photo', 'specialization']
        widgets = {
            'availability': forms.Select(choices=[('Available','Available'),('Busy','Busy'),('On Leave','On Leave')])
        }
