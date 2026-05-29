from django import forms
from .models import Visitor, Complaint


class VisitorForm(forms.ModelForm):
    class Meta:
        model  = Visitor
        fields = [
            'student_id',    'student_name',
            'visitor_name',  'visitor_email',
            'relationship',  'mobile',
            'purpose',       'visit_date',
            'checkin',       'checkout',
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. STU2024001',
            }),
            'student_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Full name of the student being visited',
            }),
            'visitor_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Full name of visitor',
            }),
            'visitor_email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'visitor@example.com',
            }),
            'relationship': forms.Select(
                attrs={'class': 'form-select form-select-lg'},
                choices=[
                    ('',         '-- Select Relationship --'),
                    ('Father',   'Father'),
                    ('Mother',   'Mother'),
                    ('Brother',  'Brother'),
                    ('Sister',   'Sister'),
                    ('Guardian', 'Guardian'),
                    ('Friend',   'Friend'),
                    ('Other',    'Other'),
                ],
            ),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '10-digit mobile number',
                'maxlength': '15',
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g. Family visit, Birthday celebration, Medical visit…',
            }),
            'visit_date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
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