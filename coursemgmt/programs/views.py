 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Course, Material, Module, Program, ProgramCourse


# ─────────────────────────────────────────────
# PROGRAM VIEWS
# ─────────────────────────────────────────────

@login_required
def program_list(request):
    qs = Program.objects.select_related("category").all()
    query = request.GET.get("q", "")
    status = request.GET.get("status", "")

    if query:
        qs = qs.filter(program_name__icontains=query) | \
             qs.filter(program_code__icontains=query) | \
             qs.filter(category__category_name__icontains=query)
        qs = qs.distinct()
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "programs/list.html", {
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "program_count": Program.objects.count(),
        "active_programs": Program.objects.filter(status="Active").count(),
        "course_count": Course.objects.count(),
    })


@login_required
def program_detail(request, pk):
    program = get_object_or_404(Program.objects.select_related("category"), pk=pk)
    links_qs = ProgramCourse.objects.filter(program=program).select_related("course").order_by("sequence_no")

    links = []
    for link in links_qs:
        link.module_count = Module.objects.filter(course=link.course).count()
        link.material_count = Material.objects.filter(module__course=link.course).count()
        links.append(link)

    course_ids = [l.course_id for l in links_qs]
    modules = Module.objects.filter(course_id__in=course_ids).select_related("course").order_by("sequence_no")
    batches = program.batches.select_related("trainer").order_by("-start_date")
    program_trainers = program.trainer_assignments.filter(is_active=True).select_related("trainer")

    return render(request, "programs/detail.html", {
        "program": program,
        "links": links,
        "modules": modules,
        "batches": batches,
        "program_trainers": program_trainers,
    })


@login_required
def program_create(request):
    from .forms import ProgramForm
    form = ProgramForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        program = form.save()
        messages.success(request, "Program created successfully.")
        return redirect("programs:detail", pk=program.pk)
    return render(request, "programs/form.html", {"form": form, "title": "Add Program"})


@login_required
def program_update(request, pk):
    from .forms import ProgramForm
    program = get_object_or_404(Program, pk=pk)
    form = ProgramForm(request.POST or None, request.FILES or None, instance=program)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Program updated.")
        return redirect("programs:detail", pk=program.pk)
    return render(request, "programs/form.html", {"form": form, "title": "Edit Program", "object": program})


@login_required
def program_delete(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == "POST":
        program.delete()
        messages.success(request, "Program deleted.")
        return redirect("programs:list")
    return render(request, "programs/confirm_delete.html", {"object": program, "title": "Delete Program"})


# ─────────────────────────────────────────────
# COURSE VIEWS
# ─────────────────────────────────────────────

@login_required
def course_list(request):
    qs = Course.objects.all()
    query = request.GET.get("q", "")
    status = request.GET.get("status", "")

    if query:
        qs = qs.filter(course_name__icontains=query) | qs.filter(course_code__icontains=query)
        qs = qs.distinct()
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "programs/courses.html", {
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "course_count": Course.objects.count(),
        "active_courses": Course.objects.filter(status="Active").count(),
        "module_count": Module.objects.count(),
    })


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    modules = course.modules.prefetch_related("materials").order_by("sequence_no")
    program_links = ProgramCourse.objects.filter(course=course).select_related("program")
    primary_trainer = course.trainer_assignments.filter(is_active=True).select_related("trainer").first()
    enrolled_students_count = course.sessions.values("batch__enrollments__student").distinct().count()

    return render(request, "programs/course_detail.html", {
        "course": course,
        "modules": modules,
        "program_links": program_links,
        "primary_trainer": primary_trainer.trainer if primary_trainer else None,
        "enrolled_students_count": enrolled_students_count,
        "module_count": modules.count(),
        "material_count": Material.objects.filter(module__course=course).count(),
    })


@login_required
def course_create(request):
    from .forms import CourseForm
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        course = form.save()
        messages.success(request, "Course created successfully.")
        return redirect("programs:course-detail", pk=course.pk)
    return render(request, "programs/form.html", {"form": form, "title": "Add Course"})


@login_required
def course_update(request, pk):
    from .forms import CourseForm
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Course updated.")
        return redirect("programs:course-detail", pk=course.pk)
    return render(request, "programs/form.html", {"form": form, "title": "Edit Course", "object": course})


@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST":
        course.delete()
        messages.success(request, "Course deleted.")
        return redirect("programs:courses")
    return render(request, "programs/confirm_delete.html", {"object": course, "title": "Delete Course"})


# ─────────────────────────────────────────────
# PROGRAM COURSE (ASSIGN)
# ─────────────────────────────────────────────

@login_required
def program_course_create(request):
    from .forms import ProgramCourseForm
    initial = {}
    if request.GET.get("program"):
        initial["program"] = request.GET.get("program")
    form = ProgramCourseForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        pc = form.save()
        messages.success(request, "Course attached to program.")
        return redirect("programs:detail", pk=pc.program.pk)
    return render(request, "programs/form.html", {"form": form, "title": "Attach Course to Program"})


@login_required
def program_course_delete(request, pk):
    pc = get_object_or_404(ProgramCourse, pk=pk)
    program_pk = pc.program.pk
    if request.method == "POST":
        pc.delete()
        messages.success(request, "Course removed from program.")
        return redirect("programs:detail", pk=program_pk)
    return render(request, "programs/confirm_delete.html", {"object": pc, "title": "Remove Course from Program"})


@login_required
def program_courses_api(request, pk):
    program = get_object_or_404(Program, pk=pk)
    courses = [
        {"id": pc.course.pk, "name": pc.course.course_name}
        for pc in ProgramCourse.objects.filter(program=program).select_related("course")
    ]
    return JsonResponse({"courses": courses})


# ─────────────────────────────────────────────
# MODULE VIEWS
# ─────────────────────────────────────────────

@login_required
def module_detail(request, pk):
    module = get_object_or_404(Module.objects.select_related("course"), pk=pk)
    materials = module.materials.all()
    return render(request, "programs/module_detail.html", {
        "module": module,
        "materials": materials,
    })


@login_required
def module_create(request):
    from .forms import ModuleForm
    initial = {}
    if request.GET.get("course"):
        initial["course"] = request.GET.get("course")
    form = ModuleForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        module = form.save()
        messages.success(request, "Module created.")
        return redirect("programs:module-detail", pk=module.pk)
    return render(request, "programs/form.html", {"form": form, "title": "Add Module"})


@login_required
def module_update(request, pk):
    from .forms import ModuleForm
    module = get_object_or_404(Module, pk=pk)
    form = ModuleForm(request.POST or None, request.FILES or None, instance=module)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Module updated.")
        return redirect("programs:module-detail", pk=module.pk)
    return render(request, "programs/form.html", {"form": form, "title": "Edit Module", "object": module})


@login_required
def module_delete(request, pk):
    module = get_object_or_404(Module, pk=pk)
    course_pk = module.course.pk
    if request.method == "POST":
        module.delete()
        messages.success(request, "Module deleted.")
        return redirect("programs:course-detail", pk=course_pk)
    return render(request, "programs/confirm_delete.html", {"object": module, "title": "Delete Module"})


# ─────────────────────────────────────────────
# MATERIAL VIEWS
# ─────────────────────────────────────────────

@login_required
def material_detail(request, pk):
    material = get_object_or_404(Material.objects.select_related("module__course", "uploaded_by"), pk=pk)
    return render(request, "programs/material_detail.html", {"material": material})


@login_required
def material_create(request):
    from .forms import MaterialForm
    initial = {}
    if request.GET.get("module"):
        initial["module"] = request.GET.get("module")
    form = MaterialForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        material = form.save(commit=False)
        material.uploaded_by = request.user
        material.save()
        messages.success(request, "Material uploaded.")
        return redirect("programs:material-detail", pk=material.pk)
    return render(request, "programs/form.html", {"form": form, "title": "Upload Material"})


@login_required
def material_update(request, pk):
    from .forms import MaterialForm
    material = get_object_or_404(Material, pk=pk)
    form = MaterialForm(request.POST or None, request.FILES or None, instance=material)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Material updated.")
        return redirect("programs:material-detail", pk=material.pk)
    return render(request, "programs/form.html", {"form": form, "title": "Edit Material", "object": material})


@login_required
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    module_pk = material.module.pk
    if request.method == "POST":
        material.delete()
        messages.success(request, "Material deleted.")
        return redirect("programs:module-detail", pk=module_pk)
    return render(request, "programs/confirm_delete.html", {"object": material, "title": "Delete Material"})