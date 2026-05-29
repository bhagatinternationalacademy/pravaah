from django.contrib import admin

from participantmgmt.models import Participant, Course, Program, ParticipantGuardian


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['admission_no', 'get_full_name', 'course', 'mobile', 'status', 'created_at']
    list_filter = ['course', 'status', 'gender']
    search_fields = ['first_name', 'last_name', 'admission_no', 'mobile', 'email']
    readonly_fields = ['created_at']

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = 'Full Name'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_name', 'level', 'duration_hours', 'fees', 'status']
    search_fields = ['course_code', 'course_name', 'level']


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['program_code', 'program_name', 'category_id', 'duration_days', 'enrollment_open', 'status']
    search_fields = ['program_code', 'program_name', 'description']


@admin.register(ParticipantGuardian)
class ParticipantGuardianAdmin(admin.ModelAdmin):
    list_display = ['guardian_name', 'participant', 'relationship', 'mobile']
    search_fields = ['guardian_name', 'participant__admission_no']


admin.site.site_header = 'PRAVAAH Administration'
admin.site.site_title = 'PRAVAAH Admin'
admin.site.index_title = 'Participant Management System'