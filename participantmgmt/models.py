from django.db import models
from django.contrib.auth.hashers import check_password, make_password


class Course(models.Model):
    course_id = models.AutoField(primary_key=True, db_column='course_id')
    course_code = models.CharField(max_length=30, unique=True)
    course_name = models.CharField(max_length=200)
    course_image = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    duration_hours = models.PositiveIntegerField(default=0)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    level = models.CharField(max_length=30)
    status = models.CharField(max_length=20, default='Active')

    class Meta:
        db_table = 'courses_tcm'

    def __str__(self):
        return self.course_name


class Program(models.Model):
    program_id = models.AutoField(primary_key=True, db_column='program_id')
    program_code = models.CharField(max_length=30, unique=True)
    program_name = models.CharField(max_length=150)
    program_image = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    duration_days = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20)
    category_id = models.BigIntegerField()
    end_date = models.DateField(null=True, blank=True)
    enrollment_open = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'programs'

    def __str__(self):
        return self.program_name

    @property
    def course_id(self):
        return self.program_id

    @property
    def course_code(self):
        return self.program_code

    @property
    def course_name(self):
        return self.program_name

    @property
    def course_image(self):
        return self.program_image or ''

    @property
    def duration_hours(self):
        return self.duration_days

    @property
    def duration_display(self):
        return f'{self.duration_days} Days'

    @property
    def fees(self):
        return None

    @property
    def fees_display(self):
        return 'To be decided'

    @property
    def level(self):
        return f'Category {self.category_id}'

    @property
    def category_label(self):
        return f'Category {self.category_id}'

    @property
    def program_status(self):
        return self.status

    @property
    def is_open(self):
        return bool(self.enrollment_open)


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
    participant_id = models.AutoField(primary_key=True, db_column='participant_id')
    user_id = models.IntegerField(null=True, blank=True, unique=True, db_column='user_id')
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    password_hash = models.CharField(max_length=128, blank=True, default='')
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
        db_table = 'participants'

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return bool(self.password_hash) and check_password(raw_password, self.password_hash)

    @property
    def is_approved(self):
        return self.status.lower() == 'approved'

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
        db_column='participant_id',
        related_name='guardians',
    )
    guardian_name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        db_table = 'participant_guardians'

    def __str__(self):
        return self.guardian_name