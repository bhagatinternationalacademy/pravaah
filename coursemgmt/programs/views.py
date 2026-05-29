from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from training_management.access import CrudFormMixin, RoleRequiredMixin, role_required

from .forms import CourseForm, MaterialForm, ModuleForm, ProgramCourseForm, ProgramForm
from .models import Course, Material, Module, Program, ProgramCourse


class ProgramListView(RoleRequiredMixin, ListView):
    model = Program
    template_name = "programs/list.html"
    paginate_by = 10
    roles = ("Admin", "Trainer", "Student")

    def get_queryset(self):
        qs = Program.objects.select_related("category")
        query = self.request.GET.get("q", "")
        if query:
            qs = qs.filter(Q(program_name__icontains=query) | Q(program_code__icontains=query) | Q(category__category_name__icontains=query))
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status__iexact=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "query": self.request.GET.get("q", ""),
                "status": self.request.GET.get("status", ""),
                "title": "Programs",
                "create_url": "programs:program-create",
                "program_count": Program.objects.count(),
                "active_programs": Program.objects.filter(status__iexact="Active").count(),
                "course_count": Course.objects.count(),
            }
        )
        return context


class ProgramDetailView(RoleRequiredMixin, DetailView):
    model = Program
    template_name = "programs/detail.html"
    context_object_name = "program"
    roles = ("Admin", "Trainer", "Student")

    def get_context_data(self, **kwargs):
        from trainers.models import CourseTrainer, ProgramTrainer
        context = super().get_context_data(**kwargs)
        
        program_courses = self.object.program_courses.select_related("course")
        course_trainers = {}
        for pc in program_courses:
            trainers = CourseTrainer.objects.filter(course=pc.course, is_active=True).select_related("trainer")
            course_trainers[pc.id] = list(trainers)
        
        program_trainers = ProgramTrainer.objects.filter(program=self.object, is_active=True).select_related("trainer")
        
        context.update(
            {
                "links": program_courses.annotate(
                    module_count=Count("course__modules", distinct=True),
                    material_count=Count("course__modules__materials", distinct=True),
                ),
                "course_trainers": course_trainers,
                "program_trainers": program_trainers,
                "modules": Module.objects.filter(course__course_program_links__program=self.object)
                .select_related("course")
                .prefetch_related("materials")
                .distinct()
                .order_by("course__course_name", "sequence_no", "module_name"),
                "batches": self.object.batches.select_related("trainer").prefetch_related("enrollments").all(),
                "course_form": ProgramCourseForm(initial={"program": self.object}),
            }
        )
        return context


class ProgramCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Program
    form_class = ProgramForm
    template_name = "shared/form.html"
    enctype = "multipart/form-data"
    roles = ("Admin",)
    success_url = reverse_lazy("programs:list")
    title = "Create Program"
    button_text = "Create"
    back_url = reverse_lazy("programs:list")

    def form_valid(self, form):
        messages.success(self.request, "Program created successfully.")
        return super().form_valid(form)

class ProgramUpdateView(ProgramCreateView, UpdateView):
    title = "Edit Program"
    button_text = "Update"

    def form_valid(self, form):
        messages.success(self.request, "Program updated successfully.")
        return super().form_valid(form)


class ProgramDeleteView(RoleRequiredMixin, DeleteView):
    model = Program
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("programs:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs.update({"title": "Delete Program", "back_url": reverse_lazy("programs:detail", args=[self.object.pk])})
        return kwargs

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Program deleted successfully.")
        return super().delete(request, *args, **kwargs)


class CourseListView(RoleRequiredMixin, ListView):
    model = Course
    template_name = "programs/courses.html"
    paginate_by = 10
    roles = ("Admin", "Trainer", "Student")

    def get_queryset(self):
        qs = Course.objects.all()
        query = self.request.GET.get("q", "")
        if query:
            qs = qs.filter(Q(course_name__icontains=query) | Q(course_code__icontains=query))
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status__iexact=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "query": self.request.GET.get("q", ""),
                "status": self.request.GET.get("status", ""),
                "title": "Courses",
                "course_count": Course.objects.count(),
                "active_courses": Course.objects.filter(status__iexact="Active").count(),
                "module_count": Module.objects.count(),
            }
        )
        return context


class CourseDetailView(RoleRequiredMixin, DetailView):
    model = Course
    template_name = "programs/course_detail.html"
    context_object_name = "course"
    roles = ("Admin", "Trainer", "Student")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        primary_session = self.object.sessions.select_related("trainer", "batch").order_by("session_date", "start_time").first()
        context.update(
            {
                "modules": self.object.modules.prefetch_related("materials").order_by("sequence_no", "module_name").all(),
                "program_links": self.object.course_program_links.select_related("program").order_by("sequence_no", "id"),
                "module_count": self.object.modules.count(),
                "material_count": Material.objects.filter(module__course=self.object).count(),
                "primary_trainer": primary_session.trainer if primary_session else None,
                "enrolled_students_count": primary_session.batch.enrollments.filter(status__iexact="Approved").count() if primary_session else 0,
            }
        )
        return context


class CourseCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    title = "Create Course"
    button_text = "Create"
    back_url = reverse_lazy("programs:courses")
    model = Course
    form_class = CourseForm
    template_name = "shared/form.html"
    enctype = "multipart/form-data"
    roles = ("Admin",)
    success_url = reverse_lazy("programs:courses")

    def form_valid(self, form):
        messages.success(self.request, "Course created successfully.")
        return super().form_valid(form)


class CourseUpdateView(CourseCreateView, UpdateView):
    title = "Edit Course"
    button_text = "Update"

    def form_valid(self, form):
        messages.success(self.request, "Course updated successfully.")
        return super().form_valid(form)


class CourseDeleteView(RoleRequiredMixin, DeleteView):
    model = Course
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("programs:courses")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs.update({"title": "Delete Course", "back_url": reverse_lazy("programs:course-detail", args=[self.object.pk])})
        return kwargs

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Course deleted successfully.")
        return super().delete(request, *args, **kwargs)


class ProgramCourseCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    title = "Assign Course to Program"
    button_text = "Assign"
    back_url = reverse_lazy("programs:list")
    model = ProgramCourse
    form_class = ProgramCourseForm
    template_name = "shared/form.html"
    roles = ("Admin",)

    def get_success_url(self):
        return reverse_lazy("programs:detail", args=[self.object.program_id])

    def get_initial(self):
        initial = super().get_initial()
        program_id = self.request.GET.get("program")
        course_id = self.request.GET.get("course")
        if program_id:
            initial["program"] = program_id
        if course_id:
            initial["course"] = course_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Course assigned to program successfully.")
        return super().form_valid(form)

class ProgramCourseDeleteView(RoleRequiredMixin, DeleteView):
    model = ProgramCourse
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)

    def get_success_url(self):
        return reverse_lazy("programs:detail", args=[self.object.program_id])

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("programs:detail", args=[self.object.program_id])
        return kwargs

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Course removed from program successfully.")
        return super().delete(request, *args, **kwargs)


class ModuleCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    title = "Create Module"
    button_text = "Create"
    back_url = reverse_lazy("programs:courses")
    model = Module
    form_class = ModuleForm
    template_name = "shared/form.html"
    enctype = "multipart/form-data"
    roles = ("Admin",)

    def get_success_url(self):
        return reverse_lazy("programs:course-detail", args=[self.object.course_id])

    def get_initial(self):
        initial = super().get_initial()
        course_id = self.request.GET.get("course")
        if course_id:
            initial["course"] = course_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Module created successfully.")
        return super().form_valid(form)

class ModuleUpdateView(ModuleCreateView, UpdateView):
    title = "Edit Module"
    button_text = "Update"


class ModuleDeleteView(RoleRequiredMixin, DeleteView):
    model = Module
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)

    def get_success_url(self):
        return reverse_lazy("programs:course-detail", args=[self.object.course_id])

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("programs:course-detail", args=[self.object.course_id])
        return kwargs

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Module deleted successfully.")
        return super().delete(request, *args, **kwargs)


class MaterialCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    title = "Upload Material"
    button_text = "Upload"
    back_url = reverse_lazy("programs:courses")
    enctype = "multipart/form-data"
    model = Material
    form_class = MaterialForm
    template_name = "shared/form.html"
    roles = ("Admin", "Trainer")

    def get_success_url(self):
        return reverse_lazy("programs:course-detail", args=[self.object.module.course_id])

    def get_initial(self):
        initial = super().get_initial()
        module_id = self.request.GET.get("module")
        if module_id:
            initial["module"] = module_id
        return initial

    def form_valid(self, form):
        if not form.cleaned_data.get("uploaded_by"):
            form.instance.uploaded_by = self.request.user
        messages.success(self.request, "Material uploaded successfully.")
        return super().form_valid(form)

class MaterialUpdateView(MaterialCreateView, UpdateView):
    title = "Edit Material"
    button_text = "Update"


class MaterialDeleteView(RoleRequiredMixin, DeleteView):
    model = Material
    template_name = "shared/confirm_delete.html"
    roles = ("Admin", "Trainer")

    def get_success_url(self):
        return reverse_lazy("programs:course-detail", args=[self.object.module.course_id])

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("programs:course-detail", args=[self.object.module.course_id])
        return kwargs

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Material deleted successfully.")
        return super().delete(request, *args, **kwargs)


class ModuleDetailView(RoleRequiredMixin, DetailView):
    model = Module
    template_name = "programs/module_detail.html"
    context_object_name = "module"
    roles = ("Admin", "Trainer", "Student")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "materials": self.object.materials.select_related("uploaded_by").order_by("-uploaded_at"),
                "course": self.object.course,
                "programs": self.object.course.course_program_links.select_related("program").order_by("sequence_no", "id"),
            }
        )
        return context


class MaterialDetailView(RoleRequiredMixin, DetailView):
    model = Material
    template_name = "programs/material_detail.html"
    context_object_name = "material"
    roles = ("Admin", "Trainer", "Student")


@role_required("Admin", "Trainer", "Student")
def program_courses_api(request, pk):
    program = Program.objects.get(pk=pk)
    payload = [
        {"id": link.course_id, "name": link.course.course_name, "code": link.course.course_code}
        for link in program.program_courses.select_related("course").order_by("sequence_no", "id")
    ]
    return JsonResponse(payload, safe=False)


program_list = ProgramListView.as_view()
program_detail = ProgramDetailView.as_view()
program_create = ProgramCreateView.as_view()
program_update = ProgramUpdateView.as_view()
program_delete = ProgramDeleteView.as_view()
course_list = CourseListView.as_view()
course_detail = CourseDetailView.as_view()
course_create = CourseCreateView.as_view()
course_update = CourseUpdateView.as_view()
course_delete = CourseDeleteView.as_view()
program_course_create = ProgramCourseCreateView.as_view()
program_course_delete = ProgramCourseDeleteView.as_view()
module_create = ModuleCreateView.as_view()
module_update = ModuleUpdateView.as_view()
module_delete = ModuleDeleteView.as_view()
material_create = MaterialCreateView.as_view()
material_update = MaterialUpdateView.as_view()
material_delete = MaterialDeleteView.as_view()
module_detail = ModuleDetailView.as_view()
material_detail = MaterialDetailView.as_view()
