"""
Forms for the Billing Management module.

Provides Django forms used by trainers to upload bills and by reviewers
to attach remarks when approving or rejecting bills.
"""

import os

from django import forms
from django.core.exceptions import ValidationError

from .models import Bill


class BillUploadForm(forms.ModelForm):
    """
    Form for trainers to submit a new bill.

    Validates that the uploaded file is a PDF and does not exceed 10 MB.
    All visible widgets are styled with Bootstrap 5 ``form-control`` class.
    """

    class Meta:
        model = Bill
        fields = [
            'bill_title',
            'bill_number',
            'bill_amount',
            'training_program',
            'bill_pdf',
        ]
        widgets = {
            'bill_title': forms.TextInput(attrs={
                'placeholder': 'Enter bill title',
            }),
            'bill_number': forms.TextInput(attrs={
                'placeholder': 'Enter unique bill number',
            }),
            'bill_amount': forms.NumberInput(attrs={
                'placeholder': 'Enter bill amount',
            }),
            'training_program': forms.TextInput(attrs={
                'placeholder': 'Enter training program name',
            }),
            'bill_pdf': forms.ClearableFileInput(attrs={
                'placeholder': 'Upload bill PDF',
            }),
        }

    def __init__(self, *args, **kwargs):
        """Apply Bootstrap 5 ``form-control`` class to every widget."""
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_classes} form-control'.strip()

    def clean_bill_pdf(self):
        """
        Validate the uploaded bill PDF.

        Raises:
            ValidationError: If the file extension is not ``.pdf`` or the
                file size exceeds 10 MB.

        Returns:
            The validated ``UploadedFile`` instance.
        """
        bill_pdf = self.cleaned_data.get('bill_pdf')
        if bill_pdf:
            # Validate file extension.
            ext = os.path.splitext(bill_pdf.name)[1].lower()
            if ext != '.pdf':
                raise ValidationError('Only PDF files are allowed.')

            # Validate file size (max 10 MB).
            max_size = 10 * 1024 * 1024  # 10 MB in bytes
            if bill_pdf.size > max_size:
                raise ValidationError(
                    'File size must not exceed 10 MB.'
                )
        return bill_pdf


class RemarkForm(forms.Form):
    """
    Simple form for capturing reviewer remarks when approving or
    rejecting a bill.
    """

    remarks = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter remarks...',
        }),
        required=True,
        help_text='Provide a reason or comment for this action.',
    )
