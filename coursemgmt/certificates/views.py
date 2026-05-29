from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.utils import timezone

from training_management.access import CrudFormMixin, RoleRequiredMixin, role_required

from .forms import CertificateForm
from .models import Certificate


class CertificateListView(RoleRequiredMixin, ListView):
    model = Certificate
    template_name = "certificates/list.html"
    paginate_by = 10
    roles = ("Admin", "Trainer", "Student")

    def get_queryset(self):
        qs = Certificate.objects.select_related("enrollment__student", "enrollment__batch")
        q = self.request.GET.get("q", "")
        if q:
            qs = qs.filter(Q(certificate_no__icontains=q) | Q(verification_code__icontains=q) | Q(enrollment__student__first_name__icontains=q) | Q(enrollment__student__last_name__icontains=q))
        status = self.request.GET.get("status", "")
        if status == "issued":
            qs = qs.filter(issue_date__isnull=False)
        elif status == "pending":
            qs = qs.filter(issue_date__isnull=True)
        elif status == "expired":
            qs = qs.filter(issue_date__isnull=False, expiry_date__lt=timezone.localdate())
        return qs


class CertificateDetailView(RoleRequiredMixin, DetailView):
    model = Certificate
    template_name = "shared/form.html"
    context_object_name = "certificate"
    roles = ("Admin", "Trainer", "Student")


class CertificateCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Certificate
    form_class = CertificateForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("certificates:list")
    title = "Issue Certificate"
    button_text = "Save"
    back_url = reverse_lazy("certificates:list")


class CertificateUpdateView(CertificateCreateView, UpdateView):
    pass


class CertificateDeleteView(RoleRequiredMixin, DeleteView):
    model = Certificate
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("certificates:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("certificates:list")
        return kwargs


@role_required("Admin", "Trainer", "Student")
def certificate_list(request):
    return CertificateListView.as_view()(request)


certificate_create = CertificateCreateView.as_view()
certificate_update = CertificateUpdateView.as_view()
certificate_delete = CertificateDeleteView.as_view()
