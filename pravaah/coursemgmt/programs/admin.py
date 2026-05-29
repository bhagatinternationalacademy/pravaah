from django.contrib import admin

from .models import AcademicYear, City, Course, CourseCategory, Gender, Material, Module, Program, ProgramCourse, RoomType, StatusMaster


for model in [AcademicYear, City, Course, CourseCategory, Gender, Material, Module, Program, ProgramCourse, RoomType, StatusMaster]:
    admin.site.register(model)
