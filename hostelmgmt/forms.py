from django import forms
from .models import Visitor, Complaint


class VisitorForm(forms.ModelForm):
    class Meta:
        model = Visitor
        fields = ['student_id', 'visitor_name', 'relationship', 'mobile', 'checkin', 'checkout']
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. STU2024001',
            }),
            'visitor_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Visitor full name',
            }),
            'relationship': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. Father, Mother, Friend',
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '10-digit mobile number',
                'maxlength': '15',
            }),
            'checkin': forms.DateTimeInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'datetime-local',
            }),
            'checkout': forms.DateTimeInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'datetime-local',
            }),
        }


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['student_id', 'room', 'complaint_type', 'description']
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Student ID',
            }),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'complaint_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the issue in detail...',
            }),
        }