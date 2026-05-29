from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from accounts.models import Role, User, UserRole
from assessments.models import Assessment, AssessmentResult
from attendance.models import Attendance
from batches.models import Batch, Enrollment, Session
from certificates.models import Certificate
from programs.models import AcademicYear, City, Course, CourseCategory, Gender, Material, Module, Program, ProgramCourse, RoomType, StatusMaster
from students.models import Student, StudentGuardian
from trainers.models import Certification, Trainer, TrainerSkill


class Command(BaseCommand):
    help = "Seed dummy training management data."

    def _svg_image(self, name: str, label: str, color: str) -> str:
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
  <defs>
    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="{color}"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="800" fill="url(#g)"/>
  <circle cx="980" cy="140" r="180" fill="rgba(255,255,255,0.12)"/>
  <circle cx="240" cy="650" r="220" fill="rgba(255,255,255,0.10)"/>
  <text x="80" y="180" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-size="68" font-weight="700">{label}</text>
  <text x="80" y="260" fill="#cbd5e1" font-family="Arial, Helvetica, sans-serif" font-size="30">Training Management</text>
</svg>"""
        return default_storage.save(name, ContentFile(svg.encode("utf-8")))

    def handle(self, *args, **options):
        admin_role, _ = Role.objects.get_or_create(role_name="Admin", defaults={"description": "Admin", "status": "Active"})
        trainer_role, _ = Role.objects.get_or_create(role_name="Trainer", defaults={"description": "Trainer", "status": "Active"})
        student_role, _ = Role.objects.get_or_create(role_name="Student", defaults={"description": "Student", "status": "Active"})

        admin_user, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com", "first_name": "Admin", "last_name": "User", "is_staff": True, "is_superuser": True, "password": make_password("admin123")})
        trainer_user, _ = User.objects.get_or_create(username="TRN001", defaults={"email": "trainer1@example.com", "first_name": "Asha", "last_name": "Sharma", "password": make_password("trainer123")})
        student_user, _ = User.objects.get_or_create(username="STD001", defaults={"email": "student1@example.com", "first_name": "Rahul", "last_name": "Verma", "password": make_password("student123")})

        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("admin123")
        admin_user.save()
        trainer_user.set_password("trainer123")
        trainer_user.save()
        student_user.set_password("student123")
        student_user.save()

        for user, role in [(admin_user, admin_role), (trainer_user, trainer_role), (student_user, student_role)]:
            UserRole.objects.get_or_create(user=user, role=role)

        male, _ = Gender.objects.get_or_create(gender_code="M", defaults={"gender_name": "Male", "status": "Active"})
        female, _ = Gender.objects.get_or_create(gender_code="F", defaults={"gender_name": "Female", "status": "Active"})
        city, _ = City.objects.get_or_create(city_code="PUNE", defaults={"city_name": "Pune", "state_name": "Maharashtra", "country_name": "India", "status": "Active"})
        category, _ = CourseCategory.objects.get_or_create(category_code="TECH", defaults={"category_name": "Technology", "description": "Technology courses", "status": "Active"})
        AcademicYear.objects.get_or_create(academic_year="2026-27", defaults={"start_date": date(2026, 6, 1), "end_date": date(2027, 3, 31), "status": "Active"})
        RoomType.objects.get_or_create(room_type_code="CLASS", defaults={"room_type_name": "Classroom", "capacity": 40, "description": "Training classroom", "status": "Active"})
        StatusMaster.objects.get_or_create(entity_name="Batch", status_code="ACTIVE", defaults={"status_name": "Active", "description": "Active status", "is_active": True})

        program, _ = Program.objects.get_or_create(program_code="PGM-DATA", defaults={"program_name": "Data Analytics Program", "category": category, "description": "Intro to analytics", "duration_days": 60, "status": "Active"})
        course1, _ = Course.objects.get_or_create(course_code="C-EXCEL", defaults={"course_name": "Excel Fundamentals", "description": "Excel basics", "duration_hours": 12, "fees": Decimal("2500"), "level": "Beginner", "status": "Active"})
        course2, _ = Course.objects.get_or_create(course_code="C-PY", defaults={"course_name": "Python Basics", "description": "Python intro", "duration_hours": 24, "fees": Decimal("5000"), "level": "Beginner", "status": "Active"})
        ProgramCourse.objects.get_or_create(program=program, course=course1, defaults={"sequence_no": 1})
        ProgramCourse.objects.get_or_create(program=program, course=course2, defaults={"sequence_no": 2})

        module1, _ = Module.objects.get_or_create(course=course1, module_name="Excel Interface", defaults={"description": "Workbook UI", "sequence_no": 1, "duration_hours": 4})
        module2, _ = Module.objects.get_or_create(course=course2, module_name="Python Syntax", defaults={"description": "Syntax basics", "sequence_no": 1, "duration_hours": 6})
        module3, _ = Module.objects.get_or_create(course=course2, module_name="Python Functions", defaults={"description": "Functions and scope", "sequence_no": 2, "duration_hours": 5})

        program_image = self._svg_image("programs/data-analytics.svg", "Data Analytics Program", "#2563eb")
        course1_image = self._svg_image("courses/excel-fundamentals.svg", "Excel Fundamentals", "#7c3aed")
        course2_image = self._svg_image("courses/python-basics.svg", "Python Basics", "#06b6d4")
        module1_image = self._svg_image("modules/excel-interface.svg", "Excel Interface", "#0f766e")
        module2_image = self._svg_image("modules/python-syntax.svg", "Python Syntax", "#f59e0b")
        module3_image = self._svg_image("modules/python-functions.svg", "Python Functions", "#ef4444")

        if not program.program_image:
            program.program_image = program_image
            program.save(update_fields=["program_image"])
        if not course1.course_image:
            course1.course_image = course1_image
            course1.save(update_fields=["course_image"])
        if not course2.course_image:
            course2.course_image = course2_image
            course2.save(update_fields=["course_image"])
        if not module1.module_image:
            module1.module_image = module1_image
            module1.save(update_fields=["module_image"])
        if not module2.module_image:
            module2.module_image = module2_image
            module2.save(update_fields=["module_image"])
        if not module3.module_image:
            module3.module_image = module3_image
            module3.save(update_fields=["module_image"])

        excel_notes = default_storage.save("materials/excel-notes.pdf", ContentFile(b"Sample training note"))
        python_slides = default_storage.save("materials/python-slides.pptx", ContentFile(b"Sample slide deck"))
        python_code = default_storage.save("materials/python-code.txt", ContentFile(b"print('hello world')"))

        excel_material, _ = Material.objects.get_or_create(module=module1, title="Excel Notes", defaults={"file_type": "PDF", "file_url": excel_notes, "uploaded_by": admin_user})
        python_material, _ = Material.objects.get_or_create(module=module2, title="Python Slides", defaults={"file_type": "PPT", "file_url": python_slides, "uploaded_by": admin_user})
        python_code_material, _ = Material.objects.get_or_create(module=module3, title="Python Practice", defaults={"file_type": "Notes", "file_url": python_code, "uploaded_by": admin_user})
        for material, path in [(excel_material, excel_notes), (python_material, python_slides), (python_code_material, python_code)]:
            if not material.file_url:
                material.file_url = path
                material.save(update_fields=["file_url"])

        trainer, _ = Trainer.objects.get_or_create(trainer_code="TRN001", defaults={"first_name": "Asha", "last_name": "Sharma", "gender": female, "dob": date(1990, 5, 10), "qualification": "MCA", "mobile": "9000000001", "email": "trainer1@example.com", "join_date": date(2025, 1, 15), "status": "Active"})
        TrainerSkill.objects.get_or_create(trainer=trainer, skill_id=1, defaults={"proficiency_level": "Advanced"})
        Certification.objects.get_or_create(trainer=trainer, certification_name="Data Trainer Cert", defaults={"issuing_authority": "Training Board", "certificate_no": "TC-001", "issue_date": date(2025, 2, 1), "expiry_date": date(2027, 2, 1), "status": "Active"})

        student, _ = Student.objects.get_or_create(student_code="STD001", defaults={"first_name": "Rahul", "last_name": "Verma", "gender": male, "dob": date(2002, 8, 12), "mobile": "9000000002", "email": "student1@example.com", "city": city, "join_date": date(2026, 5, 1), "status": "Active"})
        StudentGuardian.objects.get_or_create(student=student, guardian_name="Suresh Verma", defaults={"relation": "Father", "mobile": "9000000003", "email": "suresh@example.com", "occupation": "Engineer"})

        batch, _ = Batch.objects.get_or_create(
            batch_code="DAT_VIT_2026_DA_1",
            defaults={
                "batch_name": "Morning Batch",
                "program": program,
                "trainer": trainer,
                "client_name": "VIT",
                "subject_short_name": "DA",
                "start_date": date.today(),
                "end_date": date.today() + timedelta(days=45),
                "mode": "Offline",
                "status": "Active",
            },
        )
        batch2, _ = Batch.objects.get_or_create(
            batch_code="DAT_VIT_2026_DA_2",
            defaults={
                "batch_name": "Evening Batch",
                "program": program,
                "trainer": trainer,
                "client_name": "VIT",
                "subject_short_name": "DA",
                "start_date": date.today() + timedelta(days=1),
                "end_date": date.today() + timedelta(days=46),
                "mode": "Online",
                "status": "Planned",
            },
        )
        enrollment, _ = Enrollment.objects.get_or_create(batch=batch, student=student, defaults={"enrollment_date": date.today(), "status": "Active", "fee_amount": Decimal("5000"), "discount": Decimal("500"), "payment_status": "Paid"})
        Enrollment.objects.get_or_create(batch=batch2, student=student, defaults={"enrollment_date": date.today(), "status": "Pending", "fee_amount": Decimal("5000"), "discount": Decimal("0"), "payment_status": "Pending"})

        session1, _ = Session.objects.get_or_create(batch=batch, course=course1, trainer=trainer, session_date=date.today() + timedelta(days=20), start_time=time(9, 0), defaults={"session_topic": "Excel Basics", "end_time": time(10, 30), "meeting_link": "https://example.com/session/1", "notes": "Intro session", "recording_url": "https://example.com/recording/1"})
        session2, _ = Session.objects.get_or_create(batch=batch, course=course2, trainer=trainer, session_date=date.today() + timedelta(days=21), start_time=time(11, 0), defaults={"session_topic": "Python Intro", "end_time": time(12, 30), "meeting_link": "https://example.com/session/2", "notes": "Intro session", "recording_url": "https://example.com/recording/2"})
        session3, _ = Session.objects.get_or_create(batch=batch2, course=course2, trainer=trainer, session_date=date.today() + timedelta(days=22), start_time=time(14, 0), defaults={"session_topic": "Evening Python", "end_time": time(15, 30), "meeting_link": "https://example.com/session/3", "notes": "Evening session", "recording_url": "https://example.com/recording/3"})

        Attendance.objects.get_or_create(enrollment=enrollment, session=session1, defaults={"status": "Present"})
        Attendance.objects.get_or_create(enrollment=enrollment, session=session2, defaults={"status": "Present"})
        Attendance.objects.get_or_create(enrollment=Enrollment.objects.get(batch=batch2, student=student), session=session3, defaults={"status": "Pending"})

        assessment1, _ = Assessment.objects.get_or_create(course=course1, assessment_name="Excel Quiz", defaults={"assessment_type": "Quiz", "total_marks": 100, "passing_marks": 40, "instructions": "Answer all questions"})
        assessment2, _ = Assessment.objects.get_or_create(course=course2, assessment_name="Python Assignment", defaults={"assessment_type": "Assignment", "total_marks": 100, "passing_marks": 50, "instructions": "Submit code"})
        AssessmentResult.objects.get_or_create(enrollment=enrollment, assessment=assessment1, defaults={"marks_obtained": Decimal("85"), "status": "Pass", "submitted_at": datetime.now(), "graded_at": datetime.now()})
        AssessmentResult.objects.get_or_create(enrollment=enrollment, assessment=assessment2, defaults={"marks_obtained": Decimal("78"), "status": "Pass", "submitted_at": datetime.now(), "graded_at": datetime.now()})

        certificate, _ = Certificate.objects.get_or_create(certificate_no="CERT-001", defaults={"enrollment": enrollment, "issue_date": date.today(), "expiry_date": date.today() + timedelta(days=365), "certificate_url": "https://example.com/cert/001", "verification_code": "VER-001"})
        if certificate.enrollment_id != enrollment.enrollment_id:
            certificate.enrollment = enrollment
            certificate.save(update_fields=["enrollment"])

        self.stdout.write(self.style.SUCCESS("Dummy data seeded successfully."))
