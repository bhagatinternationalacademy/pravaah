from django.db import models


class Course(models.Model):
    course_id = models.AutoField(primary_key=True, db_column='course_id')
    course_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_years = models.IntegerField(default=0)
    level = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses'

    def __str__(self):
        return self.course_name


class AcademicYear(models.Model):
    id = models.AutoField(primary_key=True)
    year_label = models.CharField(max_length=20)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'academic_years'

    def __str__(self):
        return self.year_label


class Participant(models.Model):
    participant_id = models.AutoField(primary_key=True, db_column='student_id')
    user_id = models.IntegerField(null=True, blank=True, unique=True, db_column='user_id')
    admission_no = models.CharField(max_length=64, unique=True, db_column='admission_no')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    dob = models.DateField(null=True, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, db_column='course_id')
    academic_year_id = models.CharField(max_length=50, blank=True, db_column='academic_year_id')
    status = models.CharField(max_length=20, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'students'

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_approved(self):
        return self.status.lower() == 'active'

    @property
    def photo(self):
        return None

    @property
    def address(self):
        return ''

    @property
    def academic_year(self):
        return self.academic_year_id or ''

    def attendance_percentage(self):
        return 0


class ParticipantGuardian(models.Model):
    guardian_id = models.AutoField(primary_key=True, db_column='guardian_id')
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        db_column='student_id',
        related_name='guardians',
    )
    guardian_name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        db_table = 'student_guardians'

    def __str__(self):
        return self.guardian_name