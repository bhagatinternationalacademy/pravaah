from django.db import models

class AcademicYears(models.Model):
    id = models.BigAutoField(primary_key=True)
    year_label = models.CharField(max_length=20)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = 'academic_years'
        managed = False

class Anisha(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField()
    group_id = models.IntegerField()

    class Meta:
        db_table = 'anisha'
        managed = False

class AssessmentResults(models.Model):
    result_id = models.BigAutoField(primary_key=True)
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(max_length=20)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    assessment_id = models.IntegerField()
    enrollment_id = models.IntegerField()

    class Meta:
        db_table = 'assessment_results'
        managed = False

class Assessments(models.Model):
    assessment_id = models.BigAutoField(primary_key=True)
    assessment_name = models.CharField(max_length=150)
    assessment_type = models.CharField(max_length=60)
    total_marks = models.IntegerField()
    passing_marks = models.IntegerField()
    instructions = models.TextField()
    created_at = models.DateTimeField()
    course_id = models.IntegerField()

    class Meta:
        db_table = 'assessments'
        managed = False

class Attendance(models.Model):
    attendance_id = models.BigAutoField(primary_key=True)
    status = models.CharField(max_length=20)
    attendance_photo = models.CharField(max_length=100, null=True, blank=True)
    marked_at = models.DateTimeField()
    enrollment_id = models.IntegerField()
    session_id = models.IntegerField()

    class Meta:
        db_table = 'attendance'
        managed = False

class AuditLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    action = models.CharField(max_length=255)
    module = models.CharField(max_length=50)
    ip_address = models.CharField(max_length=39, null=True, blank=True)
    browser_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField()
    user_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'audit_logs'
        managed = False

class AuthGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150)

    class Meta:
        db_table = 'auth_group'
        managed = False

class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group_id = models.IntegerField()
    permission_id = models.IntegerField()

    class Meta:
        db_table = 'auth_group_permissions'
        managed = False

class AuthPermission(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    content_type_id = models.IntegerField()
    codename = models.CharField(max_length=100)

    class Meta:
        db_table = 'auth_permission'
        managed = False

class Batches(models.Model):
    batch_id = models.BigAutoField(primary_key=True)
    batch_code = models.CharField(max_length=30)
    batch_name = models.CharField(max_length=150)
    client_name = models.CharField(max_length=80)
    subject_short_name = models.CharField(max_length=40)
    start_date = models.DateField()
    end_date = models.DateField()
    mode = models.CharField(max_length=30)
    status = models.CharField(max_length=20)
    program_id = models.IntegerField()
    trainer_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'batches'
        managed = False

class Blocks(models.Model):
    block_id = models.BigAutoField(primary_key=True)
    block_name = models.CharField(max_length=50)
    hostel_id = models.IntegerField()

    class Meta:
        db_table = 'blocks'
        managed = False

class Certificates(models.Model):
    certificate_id = models.BigAutoField(primary_key=True)
    certificate_no = models.CharField(max_length=80)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    certificate_url = models.CharField(max_length=200)
    verification_code = models.CharField(max_length=120)
    enrollment_id = models.IntegerField()

    class Meta:
        db_table = 'certificates'
        managed = False

class Certifications(models.Model):
    certification_id = models.BigAutoField(primary_key=True)
    certification_name = models.CharField(max_length=150)
    issuing_authority = models.CharField(max_length=150)
    certificate_no = models.CharField(max_length=80)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20)
    trainer_id = models.IntegerField()

    class Meta:
        db_table = 'certifications'
        managed = False

class Cities(models.Model):
    city_id = models.BigAutoField(primary_key=True)
    city_code = models.CharField(max_length=20)
    city_name = models.CharField(max_length=120)
    state_name = models.CharField(max_length=120)
    country_name = models.CharField(max_length=120)
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'cities'
        managed = False

class Complaints(models.Model):
    complaint_id = models.BigAutoField(primary_key=True)
    student_id = models.CharField(max_length=20)
    complaint_type = models.CharField(max_length=30)
    description = models.TextField()
    complaint_date = models.DateField()
    status = models.CharField(max_length=20)
    room_id = models.IntegerField()

    class Meta:
        db_table = 'complaints'
        managed = False

class CourseCategories(models.Model):
    category_id = models.BigAutoField(primary_key=True)
    category_code = models.CharField(max_length=20)
    category_name = models.CharField(max_length=120)
    description = models.TextField()
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'course_categories'
        managed = False

class CourseTrainers(models.Model):
    id = models.BigAutoField(primary_key=True)
    assigned_date = models.DateField()
    is_active = models.BooleanField()
    course_id = models.IntegerField()
    trainer_id = models.IntegerField()

    class Meta:
        db_table = 'course_trainers'
        managed = False

class Courses(models.Model):
    course_id = models.BigAutoField(primary_key=True)
    course_code = models.CharField(max_length=30)
    course_name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    duration_years = models.IntegerField(null=True, blank=True)
    duration_hours = models.IntegerField(null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    level = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'courses'
        managed = False

class CoursesTcm(models.Model):
    course_id = models.BigAutoField(primary_key=True)
    course_code = models.CharField(max_length=30)
    course_name = models.CharField(max_length=150)
    course_image = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    duration_hours = models.IntegerField()
    fees = models.DecimalField(max_digits=10, decimal_places=2)
    level = models.CharField(max_length=30)
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'courses_tcm'
        managed = False

class Dashboard(models.Model):
    id = models.IntegerField(primary_key=True)
    cards = models.CharField(max_length=100, null=True, blank=True)
    isenabled = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'dashboard'
        managed = False

class DashboardActivityLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    action_type = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    module = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    user_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'dashboard_activity_log'
        managed = False

class DashboardActivitylog1(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_name = models.CharField(max_length=100)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField()

    class Meta:
        db_table = 'dashboard_activitylog'
        managed = False

class DashboardDashboardcard(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    total_count = models.IntegerField()
    is_active = models.BooleanField()
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'dashboard_dashboardcard'
        managed = False

class DashboardNotification(models.Model):
    id = models.BigAutoField(primary_key=True)
    message = models.TextField()
    created_at = models.DateTimeField()
    is_read = models.BooleanField()

    class Meta:
        db_table = 'dashboard_notification'
        managed = False

class DashboardQuickLinks(models.Model):
    id = models.BigAutoField(primary_key=True)
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    icon = models.CharField(max_length=60)
    colour = models.CharField(max_length=30)
    order = models.IntegerField()
    is_active = models.BooleanField()

    class Meta:
        db_table = 'dashboard_quick_links'
        managed = False

class DjangoAdminLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    action_time = models.DateTimeField()
    object_id = models.TextField(null=True, blank=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.IntegerField()
    change_message = models.TextField()
    content_type_id = models.IntegerField(null=True, blank=True)
    user_id = models.IntegerField()

    class Meta:
        db_table = 'django_admin_log'
        managed = False

class DjangoContentType(models.Model):
    id = models.BigAutoField(primary_key=True)
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        db_table = 'django_content_type'
        managed = False

class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        db_table = 'django_migrations'
        managed = False

class DjangoSession(models.Model):
    session_key = models.CharField(max_length=40, primary_key=True)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        db_table = 'django_session'
        managed = False

class Enrollments(models.Model):
    enrollment_id = models.BigAutoField(primary_key=True)
    enrollment_date = models.DateField()
    status = models.CharField(max_length=20)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20)
    batch_id = models.IntegerField()
    student_id = models.IntegerField()

    class Meta:
        db_table = 'enrollments'
        managed = False

class FeePayments(models.Model):
    payment_id = models.BigAutoField(primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=30)
    receipt_no = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20)
    allocation_id = models.IntegerField()

    class Meta:
        db_table = 'fee_payments'
        managed = False

class Floors(models.Model):
    floor_id = models.BigAutoField(primary_key=True)
    floor_no = models.IntegerField()
    block_id = models.IntegerField()

    class Meta:
        db_table = 'floors'
        managed = False

class GauravUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True, blank=True)
    is_superuser = models.BooleanField()
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    email = models.CharField(max_length=254)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    is_email_verified = models.BooleanField()
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    token_created_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'gaurav_user'
        managed = False

class GauravUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField()
    group_id = models.IntegerField()

    class Meta:
        db_table = 'gaurav_user_groups'
        managed = False

class GauravUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField()
    permission_id = models.IntegerField()

    class Meta:
        db_table = 'gaurav_user_user_permissions'
        managed = False

class Genders(models.Model):
    gender_id = models.BigAutoField(primary_key=True)
    gender_code = models.CharField(max_length=20)
    gender_name = models.CharField(max_length=40)
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'genders'
        managed = False

class HostelmgmtBlock(models.Model):
    block_id = models.BigAutoField(primary_key=True)
    block_name = models.CharField(max_length=50)

    class Meta:
        db_table = 'hostelmgmt_block'
        managed = False

class HostelmgmtFloor(models.Model):
    floor_id = models.BigAutoField(primary_key=True)
    floor_no = models.IntegerField()
    block_id = models.IntegerField()

    class Meta:
        db_table = 'hostelmgmt_floor'
        managed = False

class HostelmgmtHostel(models.Model):
    hostel_id = models.BigAutoField(primary_key=True)
    hostel_code = models.CharField(max_length=20)
    hostel_name = models.CharField(max_length=100)
    address = models.TextField()
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'hostelmgmt_hostel'
        managed = False

class HostelmgmtVisitor(models.Model):
    visitor_id = models.BigAutoField(primary_key=True)
    student_id = models.CharField(max_length=20)
    visitor_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    mobile = models.CharField(max_length=15)
    checkin = models.DateTimeField()
    checkout = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'hostelmgmt_visitor'
        managed = False

class Hostels(models.Model):
    hostel_id = models.BigAutoField(primary_key=True)
    hostel_code = models.CharField(max_length=20)
    hostel_name = models.CharField(max_length=100)
    address = models.TextField()
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'hostels'
        managed = False

class MaintenanceRequests(models.Model):
    request_id = models.BigAutoField(primary_key=True)
    request_date = models.DateField()
    description = models.TextField()
    status = models.CharField(max_length=20)
    resolved_on = models.DateField(null=True, blank=True)
    requested_by_id = models.IntegerField(null=True, blank=True)
    room_id = models.IntegerField()

    class Meta:
        db_table = 'maintenance_requests'
        managed = False

class Materials(models.Model):
    material_id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=150)
    file_type = models.CharField(max_length=40)
    file_url = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField()
    uploaded_by = models.IntegerField(null=True, blank=True)
    module_id = models.IntegerField()

    class Meta:
        db_table = 'materials'
        managed = False

class Modules(models.Model):
    module_id = models.BigAutoField(primary_key=True)
    module_name = models.CharField(max_length=150)
    module_image = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    sequence_no = models.IntegerField()
    duration_hours = models.IntegerField()
    course_id = models.IntegerField()

    class Meta:
        db_table = 'modules'
        managed = False

class ParticipantGuardians(models.Model):
    guardian_id = models.BigAutoField(primary_key=True)
    participant_id = models.IntegerField()
    guardian_name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=50, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    email = models.CharField(max_length=254, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'participant_guardians'
        managed = False

class Participants(models.Model):
    participant_id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField(null=True, blank=True)
    admission_no = models.CharField(max_length=64)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    email = models.CharField(max_length=254, null=True, blank=True)
    course_id = models.IntegerField(null=True, blank=True)
    academic_year_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'participants'
        managed = False

class ProgramCourses(models.Model):
    id = models.BigAutoField(primary_key=True)
    sequence_no = models.IntegerField()
    course_id = models.IntegerField()
    program_id = models.IntegerField()

    class Meta:
        db_table = 'program_courses'
        managed = False

class ProgramTrainers(models.Model):
    id = models.BigAutoField(primary_key=True)
    specialization = models.CharField(max_length=200)
    assigned_date = models.DateField()
    is_active = models.BooleanField()
    program_id = models.IntegerField()
    trainer_id = models.IntegerField()

    class Meta:
        db_table = 'program_trainers'
        managed = False

class Programs(models.Model):
    program_id = models.BigAutoField(primary_key=True)
    program_code = models.CharField(max_length=30)
    program_name = models.CharField(max_length=150)
    program_image = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    duration_days = models.IntegerField()
    status = models.CharField(max_length=20)
    category_id = models.IntegerField()

    class Meta:
        db_table = 'programs'
        managed = False

class Roles(models.Model):
    role_id = models.BigAutoField(primary_key=True)
    role_name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'roles'
        managed = False

class RoomAllocations(models.Model):
    allocation_id = models.BigAutoField(primary_key=True)
    student_id = models.CharField(max_length=50)
    student_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    bed_number = models.IntegerField()
    allocation_date = models.DateField()
    checkout_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20)
    room_id = models.IntegerField()
    person_type = models.CharField(max_length=10)
    checkin_date = models.DateField(null=True, blank=True)
    actual_checkout_time = models.DateTimeField(null=True, blank=True)
    checked_out_by_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'room_allocations'
        managed = False

class RoomTransfers(models.Model):
    transfer_id = models.BigAutoField(primary_key=True)
    student_id = models.CharField(max_length=50)
    reason = models.TextField()
    request_date = models.DateField()
    status = models.CharField(max_length=20)
    from_room_id = models.IntegerField()
    to_room_id = models.IntegerField()
    student_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'room_transfers'
        managed = False

class RoomTypes(models.Model):
    room_type_id = models.BigAutoField(primary_key=True)
    room_type_code = models.CharField(max_length=20)
    room_type_name = models.CharField(max_length=120)
    capacity = models.IntegerField()
    description = models.TextField()
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'room_types'
        managed = False

class Rooms(models.Model):
    room_id = models.BigAutoField(primary_key=True)
    room_number = models.CharField(max_length=10)
    capacity = models.IntegerField()
    occupied = models.IntegerField()
    gender = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=20)
    floor_id = models.IntegerField()

    class Meta:
        db_table = 'rooms'
        managed = False

class Sessions(models.Model):
    session_id = models.BigAutoField(primary_key=True)
    session_topic = models.CharField(max_length=200)
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    meeting_link = models.CharField(max_length=200)
    notes = models.TextField()
    recording_url = models.CharField(max_length=200)
    batch_id = models.IntegerField()
    course_id = models.IntegerField()
    trainer_id = models.IntegerField()

    class Meta:
        db_table = 'sessions'
        managed = False

class StatusMaster(models.Model):
    status_master_id = models.BigAutoField(primary_key=True)
    entity_name = models.CharField(max_length=80)
    status_code = models.CharField(max_length=40)
    status_name = models.CharField(max_length=80)
    description = models.TextField()
    is_active = models.BooleanField()

    class Meta:
        db_table = 'status_master'
        managed = False

class StudentGuardians(models.Model):
    guardian_id = models.BigAutoField(primary_key=True)
    guardian_name = models.CharField(max_length=150)
    relation = models.CharField(max_length=60)
    mobile = models.CharField(max_length=20)
    email = models.CharField(max_length=254)
    occupation = models.CharField(max_length=120)
    student_id = models.IntegerField()

    class Meta:
        db_table = 'student_guardians'
        managed = False

class Students(models.Model):
    student_id = models.BigAutoField(primary_key=True)
    student_code = models.CharField(max_length=30)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    dob = models.DateField(null=True, blank=True)
    mobile = models.CharField(max_length=20)
    email = models.CharField(max_length=254)
    join_date = models.DateField()
    status = models.CharField(max_length=20)
    city_id = models.IntegerField(null=True, blank=True)
    gender = models.IntegerField()

    class Meta:
        db_table = 'students'
        managed = False

class StudentsAttendance(models.Model):
    id = models.BigAutoField(primary_key=True)
    date = models.DateField()
    subject = models.CharField(max_length=100)
    status = models.CharField(max_length=10)
    remarks = models.CharField(max_length=200)
    created_at = models.DateTimeField()
    student_id = models.IntegerField()

    class Meta:
        db_table = 'students_attendance'
        managed = False

class StudentsNotification(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_global = models.BooleanField()
    created_at = models.DateTimeField()
    is_read = models.BooleanField()
    student_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'students_notification'
        managed = False

class StudentsResult(models.Model):
    id = models.BigAutoField(primary_key=True)
    subject = models.CharField(max_length=100)
    semester = models.CharField(max_length=20)
    max_marks = models.IntegerField()
    obtained_marks = models.IntegerField()
    grade = models.CharField(max_length=5)
    remarks = models.CharField(max_length=200)
    created_at = models.DateTimeField()
    student_id = models.IntegerField()

    class Meta:
        db_table = 'students_result'
        managed = False

class Test(models.Model):
    uid = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=68, null=True, blank=True)

    class Meta:
        db_table = 'test'
        managed = False

class TrainerPayments(models.Model):
    payment_id = models.BigAutoField(primary_key=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_mode = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=100)
    hours_billed = models.IntegerField()
    status = models.CharField(max_length=20)
    remarks = models.TextField(null=True, blank=True)
    trainer_id = models.IntegerField()

    class Meta:
        db_table = 'trainer_payments'
        managed = False

class TrainerSkills(models.Model):
    id = models.BigAutoField(primary_key=True)
    skill_id = models.IntegerField()
    proficiency_level = models.CharField(max_length=50)
    trainer_id = models.IntegerField()

    class Meta:
        db_table = 'trainer_skills'
        managed = False

class Trainers(models.Model):
    trainer_id = models.BigAutoField(primary_key=True)
    trainer_code = models.CharField(max_length=30)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    dob = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=150)
    mobile = models.CharField(max_length=20)
    email = models.CharField(max_length=254)
    join_date = models.DateField()
    status = models.CharField(max_length=20)
    gender = models.IntegerField()

    class Meta:
        db_table = 'trainers'
        managed = False

class UserRoles(models.Model):
    user_role_id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField()
    role_id = models.IntegerField()

    class Meta:
        db_table = 'user_roles'
        managed = False

class Users(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True, blank=True)
    is_superuser = models.BooleanField()
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        db_table = 'users'
        managed = False

class Visitors(models.Model):
    visitor_id = models.BigAutoField(primary_key=True)
    student_id = models.CharField(max_length=20)
    visitor_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    mobile = models.CharField(max_length=15)
    checkin = models.DateTimeField()
    checkout = models.DateTimeField(null=True, blank=True)
    purpose = models.TextField()
    student_name = models.CharField(max_length=100)
    visit_date = models.DateField(null=True, blank=True)
    visitor_email = models.CharField(max_length=150)

    class Meta:
        db_table = 'visitors'
        managed = False

class WaitingList(models.Model):
    waiting_id = models.BigAutoField(primary_key=True)
    person_type = models.CharField(max_length=10)
    person_id = models.CharField(max_length=50)
    person_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    checkin_date = models.DateField(null=True, blank=True)
    checkout_date = models.DateField(null=True, blank=True)
    added_on = models.DateField()
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'waiting_list'
        managed = False

