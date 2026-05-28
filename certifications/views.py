from django.shortcuts import render, redirect
from .models import Certification
from trainers.models import Trainer
from django.contrib.auth.decorators import login_required
from .forms import CertificationForm


@login_required
def certification_list(request):
    certs = Certification.objects.all()
    return render(request, 'certifications/certification_list.html', {'certs': certs})


@login_required
def certification_add(request):
    if request.method == 'POST':
        form = CertificationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('certifications:list')
    else:
        form = CertificationForm()
    return render(request, 'certifications/certification_add.html', {'form': form})
