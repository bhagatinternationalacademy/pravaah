from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from batches.models import Session
from programs.models import Course
from training_management.access import CrudFormMixin, RoleRequiredMixin, role_required

from .forms import CertificationForm, TrainerForm, TrainerSkillForm, ProgramTrainerForm, CourseTrainerForm
from .models import Certification, Trainer, TrainerSkill, ProgramTrainer, CourseTrainer


def resolve_trainer(user):
    return Trainer.objects.filter(email=user.email).first() or Trainer.objects.filter(trainer_code=user.username).first()


class TrainerListView(RoleRequiredMixin, ListView):
    model = Trainer
    template_name = "trainers/list.html"
    paginate_by = 10
    roles = ("Admin", "Trainer")

    def get_queryset(self):
        qs = Trainer.objects.select_related("gender")
        q = self.request.GET.get("q", "")
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(trainer_code__icontains=q) | Q(email__icontains=q))
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status__iexact=status)
        return qs


class TrainerDetailView(RoleRequiredMixin, DetailView):
    model = Trainer
    template_name = "trainers/detail.html"
    context_object_name = "trainer"
    roles = ("Admin", "Trainer")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["skills"] = self.object.skills.all()
        kwargs["certifications"] = self.object.certifications.all()
        kwargs["sessions"] = self.object.sessions.select_related("batch", "course").all()
        kwargs["batches"] = self.object.batches.select_related("program").all()
        kwargs["programs"] = self.object.program_assignments.select_related("program").filter(is_active=True)
        kwargs["courses"] = self.object.course_assignments.select_related("course").filter(is_active=True)
        return kwargs


class TrainerCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Trainer
    form_class = TrainerForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:list")
    title = "Create Trainer"
    button_text = "Create"
    back_url = reverse_lazy("trainers:list")


class TrainerUpdateView(TrainerCreateView, UpdateView):
    pass


class TrainerDeleteView(RoleRequiredMixin, DeleteView):
    model = Trainer
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("trainers:detail", args=[self.object.pk])
        return kwargs


class TrainerSkillCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = TrainerSkill
    form_class = TrainerSkillForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:list")
    title = "Add Trainer Skill"
    button_text = "Save"
    back_url = reverse_lazy("trainers:list")

    def get_initial(self):
        initial = super().get_initial()
        trainer_id = self.request.GET.get("trainer")
        if trainer_id:
            initial["trainer"] = trainer_id
        return initial


class TrainerSkillUpdateView(TrainerSkillCreateView, UpdateView):
    pass


class TrainerSkillDeleteView(RoleRequiredMixin, DeleteView):
    model = TrainerSkill
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("trainers:list")
        return kwargs


class CertificationCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Certification
    form_class = CertificationForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:list")
    title = "Add Certification"
    button_text = "Save"
    back_url = reverse_lazy("trainers:list")

    def get_initial(self):
        initial = super().get_initial()
        trainer_id = self.request.GET.get("trainer")
        if trainer_id:
            initial["trainer"] = trainer_id
        return initial


class CertificationUpdateView(CertificationCreateView, UpdateView):
    pass


class CertificationDeleteView(RoleRequiredMixin, DeleteView):
    model = Certification
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("trainers:list")
        return kwargs


@role_required("Admin", "Trainer")
def dashboard(request):
    trainer = resolve_trainer(request.user)
    sessions = Session.objects.filter(trainer=trainer).select_related("batch", "course")[:10] if trainer else Session.objects.none()
    return render(request, "trainers/dashboard.html", {"trainer": trainer, "sessions": sessions})


@role_required("Admin")
def availability(request):
    trainer_id = request.GET.get("trainer")
    trainer = Trainer.objects.filter(pk=trainer_id).first() if trainer_id else None
    schedules = Session.objects.select_related("trainer", "batch", "course")
    if trainer:
        schedules = schedules.filter(trainer=trainer)
    return render(request, "trainers/availability.html", {"trainers": Trainer.objects.all(), "trainer": trainer, "schedules": schedules[:50], "courses": Course.objects.all()})


class ProgramTrainerListView(RoleRequiredMixin, ListView):
    model = ProgramTrainer
    template_name = "trainers/program_trainer_list.html"
    context_object_name = "program_trainers"
    paginate_by = 20
    roles = ("Admin",)

    def get_queryset(self):
        qs = ProgramTrainer.objects.select_related("trainer", "program")
        q = self.request.GET.get("q", "")
        if q:
            qs = qs.filter(Q(trainer__first_name__icontains=q) | Q(trainer__last_name__icontains=q) | Q(program__program_name__icontains=q))
        is_active = self.request.GET.get("is_active", "")
        if is_active:
            qs = qs.filter(is_active=(is_active == "true"))
        return qs


class ProgramTrainerCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = ProgramTrainer
    form_class = ProgramTrainerForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:program-trainer-list")
    title = "Assign Trainer to Program"
    button_text = "Assign"
    back_url = reverse_lazy("trainers:program-trainer-list")


class ProgramTrainerUpdateView(ProgramTrainerCreateView, UpdateView):
    title = "Update Program Trainer Assignment"
    button_text = "Update"


class ProgramTrainerDeleteView(RoleRequiredMixin, DeleteView):
    model = ProgramTrainer
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:program-trainer-list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("trainers:program-trainer-list")
        return kwargs


class CourseTrainerListView(RoleRequiredMixin, ListView):
    model = CourseTrainer
    template_name = "trainers/course_trainer_list.html"
    context_object_name = "course_trainers"
    paginate_by = 20
    roles = ("Admin",)

    def get_queryset(self):
        qs = CourseTrainer.objects.select_related("trainer", "course")
        q = self.request.GET.get("q", "")
        if q:
            qs = qs.filter(Q(trainer__first_name__icontains=q) | Q(trainer__last_name__icontains=q) | Q(course__course_name__icontains=q))
        is_active = self.request.GET.get("is_active", "")
        if is_active:
            qs = qs.filter(is_active=(is_active == "true"))
        return qs


class CourseTrainerCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = CourseTrainer
    form_class = CourseTrainerForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:course-trainer-list")
    title = "Assign Trainer to Course"
    button_text = "Assign"
    back_url = reverse_lazy("trainers:course-trainer-list")


class CourseTrainerUpdateView(CourseTrainerCreateView, UpdateView):
    title = "Update Course Trainer Assignment"
    button_text = "Update"


class CourseTrainerDeleteView(RoleRequiredMixin, DeleteView):
    model = CourseTrainer
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("trainers:course-trainer-list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("trainers:course-trainer-list")
        return kwargs


trainer_list = TrainerListView.as_view()
trainer_detail = TrainerDetailView.as_view()
trainer_create = TrainerCreateView.as_view()
trainer_update = TrainerUpdateView.as_view()
trainer_delete = TrainerDeleteView.as_view()
trainer_skill_create = TrainerSkillCreateView.as_view()
trainer_skill_update = TrainerSkillUpdateView.as_view()
trainer_skill_delete = TrainerSkillDeleteView.as_view()
certification_create = CertificationCreateView.as_view()
certification_update = CertificationUpdateView.as_view()
certification_delete = CertificationDeleteView.as_view()
program_trainer_list = ProgramTrainerListView.as_view()
program_trainer_create = ProgramTrainerCreateView.as_view()
program_trainer_update = ProgramTrainerUpdateView.as_view()
program_trainer_delete = ProgramTrainerDeleteView.as_view()
course_trainer_list = CourseTrainerListView.as_view()
course_trainer_create = CourseTrainerCreateView.as_view()
course_trainer_update = CourseTrainerUpdateView.as_view()
course_trainer_delete = CourseTrainerDeleteView.as_view()
