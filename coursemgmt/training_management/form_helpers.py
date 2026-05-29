from django import forms


class BootstrapModelForm(forms.ModelForm):
    file_fields = {"FileInput", "ClearableFileInput"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            widget_type = widget.__class__.__name__
            classes = widget.attrs.get("class", "").split()
            if widget_type in self.file_fields:
                classes = [cls for cls in classes if cls != "form-control"]
                classes.append("form-control")
            elif widget_type == "Select":
                classes.append("form-select")
            elif widget_type in {"CheckboxInput", "CheckboxSelectMultiple"}:
                classes = [cls for cls in classes if cls != "form-control"]
                classes.append("form-check-input")
            elif widget_type in {"DateInput", "TimeInput", "NumberInput", "EmailInput", "URLInput", "TextInput", "Textarea"}:
                classes.append("form-control")
            else:
                classes.append("form-control")
            widget.attrs["class"] = " ".join(sorted(set(classes))).strip()


ACTIVE_INACTIVE_CHOICES = [
    ("Active", "Active"),
    ("Inactive", "Inactive"),
]

BATCH_STATUS_CHOICES = [
    ("Planned", "Planned"),
    ("Active", "Active"),
    ("Completed", "Completed"),
    ("On Hold", "On Hold"),
]

ENROLLMENT_STATUS_CHOICES = [
    ("Approved", "Approved"),
    ("Rejected", "Rejected"),
]

ATTENDANCE_STATUS_CHOICES = [
    ("Present", "Present"),
    ("Absent", "Absent"),
    ("Late", "Late"),
    ("Excused", "Excused"),
]

ASSESSMENT_RESULT_STATUS_CHOICES = [
    ("Pending", "Pending"),
    ("Pass", "Pass"),
    ("Fail", "Fail"),
]

CERTIFICATE_STATUS_CHOICES = [
    ("Active", "Active"),
    ("Expired", "Expired"),
]
