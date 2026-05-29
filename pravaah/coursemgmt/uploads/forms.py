from django import forms


class ExcelUploadForm(forms.Form):
    import_type = forms.ChoiceField(
        choices=[
            ("trainers", "Trainers"),
            ("students", "Students"),
            ("certificates", "Certificates"),
            ("assessment_results", "Assessment Results"),
        ]
    )
    file = forms.FileField()
