from django import forms

from batches.models import Enrollment, Session
from training_management.form_helpers import ATTENDANCE_STATUS_CHOICES, BootstrapModelForm

from .models import Attendance


class AttendanceForm(BootstrapModelForm):
    status = forms.ChoiceField(choices=ATTENDANCE_STATUS_CHOICES)

    class Meta:
        model = Attendance
        fields = ["enrollment", "session", "status", "attendance_photo"]

    def __init__(self, *args, **kwargs):
        batch_id = kwargs.pop("batch_id", None)
        super().__init__(*args, **kwargs)
        enrollment_qs = Enrollment.objects.select_related("batch", "student").order_by("batch__batch_name", "student__first_name")
        session_qs = Session.objects.select_related("batch", "course", "trainer").order_by("session_date", "start_time")
        if batch_id:
            enrollment_qs = enrollment_qs.filter(batch_id=batch_id)
            session_qs = session_qs.filter(batch_id=batch_id)
        self.fields["enrollment"].queryset = enrollment_qs
        self.fields["session"].queryset = session_qs

    def clean(self):
        cleaned = super().clean()
        enrollment = cleaned.get("enrollment")
        session = cleaned.get("session")
        if enrollment and session and enrollment.batch_id != session.batch_id:
            raise forms.ValidationError("Attendance enrollment and session must belong to the same batch.")
        return cleaned
