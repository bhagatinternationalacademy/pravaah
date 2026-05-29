from django import forms

from training_management.form_helpers import ACTIVE_INACTIVE_CHOICES, BootstrapModelForm

from .models import AcademicYear, City, Course, CourseCategory, Gender, Material, Module, Program, ProgramCourse, RoomType, StatusMaster


class ProgramForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=ACTIVE_INACTIVE_CHOICES)

    class Meta:
        model = Program
        fields = ["program_name", "category", "program_image", "description", "duration_days", "start_date", "end_date", "enrollment_open", "status"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class CourseForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=ACTIVE_INACTIVE_CHOICES)

    class Meta:
        model = Course
        fields = ["course_name", "course_image", "description", "duration_hours", "fees", "level", "status"]


class ProgramCourseForm(BootstrapModelForm):
    class Meta:
        model = ProgramCourse
        fields = ["program", "course", "sequence_no"]


class ModuleForm(BootstrapModelForm):
    class Meta:
        model = Module
        fields = ["course", "module_name", "module_image", "description", "sequence_no", "duration_hours"]


class MaterialForm(BootstrapModelForm):
    class Meta:
        model = Material
        fields = ["module", "title", "file_type", "file_url", "uploaded_by"]
        widgets = {"uploaded_by": forms.HiddenInput()}

    def clean_file_url(self):
        uploaded = self.cleaned_data["file_url"]
        allowed = {".pdf", ".ppt", ".pptx", ".txt", ".mp4", ".mov", ".m4v", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
        ext = uploaded.name.lower().rsplit(".", 1)[-1] if "." in uploaded.name else ""
        if ext and f".{ext}" not in allowed:
            raise forms.ValidationError("Unsupported material file type.")
        return uploaded
