from django import forms
from .models import RoomAllocation, Visitor, Complaint


class RoomAllocationForm(forms.ModelForm):
    """Form for allocating a room to a student."""
    class Meta:
        model = RoomAllocation
        fields = ['student_id', 'student_name', 'gender']
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. STU2024001',
            }),
            'student_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Full name of student',
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
        }
        labels = {
            'student_id': 'Student ID',
            'student_name': 'Student Full Name',
            'gender': 'Gender',
        }


class VisitorForm(forms.ModelForm):
    """Form for registering a visitor and booking a gate pass."""
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
    """Form for submitting a hostel complaint."""
    class Meta:
        model = Complaint
        fields = ['student_id', 'room', 'complaint_type', 'description']
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Student ID',
            }),
            'room': forms.Select(attrs={
                'class': 'form-select',
            }),
            'complaint_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the issue in detail...',
            }),
        }