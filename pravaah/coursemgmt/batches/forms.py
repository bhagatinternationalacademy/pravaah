from django import forms

from programs.models import Course, ProgramCourse
from students.models import Student
from trainers.models import Trainer
from training_management.form_helpers import BATCH_STATUS_CHOICES, ENROLLMENT_STATUS_CHOICES, BootstrapModelForm

from .models import Batch, Enrollment, Session


class BatchForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=BATCH_STATUS_CHOICES)

    class Meta:
        model = Batch
        fields = ["batch_name", "program", "trainer", "client_name", "subject_short_name", "start_date", "end_date", "mode", "status"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}), "end_date": forms.DateInput(attrs={"type": "date"})}


class EnrollmentForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=ENROLLMENT_STATUS_CHOICES)

    class Meta:
        model = Enrollment
        fields = ["batch", "student", "enrollment_date", "status", "fee_amount", "discount", "payment_status"]
        widgets = {"enrollment_date": forms.DateInput(attrs={"type": "date"})}


class EnrollmentRequestForm(BootstrapModelForm):
    class Meta:
        model = Enrollment
        fields = ["batch", "student"]


class SessionForm(BootstrapModelForm):
    class Meta:
        model = Session
        fields = ["batch", "course", "trainer", "session_topic", "session_date", "start_time", "end_time", "meeting_link", "notes", "recording_url"]
        widgets = {
            "session_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }


class BatchFormationForm(BootstrapModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.none(), label="Course")
    status = forms.ChoiceField(choices=BATCH_STATUS_CHOICES)
    participants = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Participants",
    )
    generate_session_plan = forms.BooleanField(required=False, initial=True, label="Generate session plan")

    class Meta:
        model = Batch
        fields = ["batch_name", "program", "course", "trainer", "client_name", "subject_short_name", "start_date", "end_date", "mode", "status"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}), "end_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        program_key = self.add_prefix("program")

        self.fields["trainer"].required = True
        self.fields["course"].required = True
        self.fields["trainer"].queryset = Trainer.objects.filter(status__iexact="Active").select_related("gender")
        self.fields["course"].queryset = Course.objects.all().order_by("course_name")
        self.fields["participants"].queryset = Student.objects.filter(status__iexact="Active", enrollments__status__iexact="Approved").distinct().order_by("first_name", "last_name")

        program_id = self.data.get(program_key) or self.initial.get("program") or getattr(self.instance, "program_id", None)
        if program_id:
            self.fields["course"].queryset = Course.objects.filter(course_program_links__program_id=program_id).distinct().order_by("course_name")
            students = Student.objects.filter(status__iexact="Active", enrollments__status__iexact="Approved").distinct()
            current_batch_id = getattr(self.instance, "pk", None)
            occupied_students = Student.objects.filter(enrollments__batch__status__in=["Active", "Planned"]).distinct()
            if current_batch_id:
                occupied_students = occupied_students.exclude(enrollments__batch_id=current_batch_id)
            self.fields["participants"].queryset = students.exclude(pk__in=occupied_students.values_list("pk", flat=True)).order_by("first_name", "last_name")

        if self.instance and self.instance.pk:
            selected_students = self.instance.enrollments.filter(status__iexact="Approved").values_list("student_id", flat=True)
            self.initial.setdefault("participants", list(selected_students))
            primary_course = self.instance.sessions.select_related("course").order_by("session_date", "start_time").first()
            if primary_course:
                self.initial.setdefault("course", primary_course.course_id)

    def clean(self):
        cleaned = super().clean()
        program = cleaned.get("program")
        course = cleaned.get("course")
        trainer = cleaned.get("trainer")
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")
        instance = self.instance if getattr(self.instance, "pk", None) else None

        if program and course and not ProgramCourse.objects.filter(program=program, course=course).exists():
            raise forms.ValidationError({"course": "Selected course must belong to the chosen program."})

        if trainer and start_date and end_date:
            from .models import Session

            conflicting = Session.objects.filter(trainer=trainer, session_date__range=(start_date, end_date))
            if instance:
                conflicting = conflicting.exclude(batch=instance)
            if conflicting.exists():
                raise forms.ValidationError({"trainer": "Trainer already has sessions in this batch date range."})

        cleaned["participants"] = cleaned.get("participants") or []
        return cleaned
