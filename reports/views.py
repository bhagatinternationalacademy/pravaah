from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from trainers.models import Trainer
from skills.models import TrainerSkill, Skill
from certifications.models import Certification
from django.http import HttpResponse
import csv
from django.utils import timezone
from datetime import timedelta


@login_required
def trainer_reports(request):
    # Filters
    status = request.GET.get('status', '').strip()
    availability = request.GET.get('availability', '').strip()
    skill_id = request.GET.get('skill', '').strip()

    trainers_qs = Trainer.objects.all()
    if status:
        trainers_qs = trainers_qs.filter(status__iexact=status)
    if availability:
        trainers_qs = trainers_qs.filter(availability__iexact=availability)
    if skill_id:
        trainers_qs = trainers_qs.filter(trainerskill__skill_id=skill_id).distinct()

    total = trainers_qs.count()

    # certification reports
    today = timezone.now().date()
    expiring = Certification.objects.filter(expiry_date__isnull=False, expiry_date__lte=today + timedelta(days=30), expiry_date__gte=today)
    expired = Certification.objects.filter(expiry_date__isnull=False, expiry_date__lt=today)

    skills = Skill.objects.all()

    context = {
        'trainers': trainers_qs,
        'total': total,
        'expiring_count': expiring.count(),
        'expired_count': expired.count(),
        'skills': skills,
    }
    return render(request, 'reports/trainer_reports.html', context)


@login_required
def export_trainers_csv(request):
    # same filters
    status = request.GET.get('status', '').strip()
    availability = request.GET.get('availability', '').strip()
    skill_id = request.GET.get('skill', '').strip()

    trainers_qs = Trainer.objects.all()
    if status:
        trainers_qs = trainers_qs.filter(status__iexact=status)
    if availability:
        trainers_qs = trainers_qs.filter(availability__iexact=availability)
    if skill_id:
        trainers_qs = trainers_qs.filter(trainerskill__skill_id=skill_id).distinct()

    # build CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="trainers_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Trainer Code', 'First Name', 'Last Name', 'Qualification', 'Specialization', 'Mobile', 'Email', 'Status', 'Availability', 'Joining Date'])
    for t in trainers_qs:
        writer.writerow([t.trainer_code, t.first_name, t.last_name, t.qualification, t.specialization, t.mobile, t.email, t.status, t.availability, t.joining_date])
    return response


@login_required
def export_certifications_csv(request):
    # export certifications with status
    certs = Certification.objects.select_related('trainer').all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="certifications_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Trainer', 'Certification', 'Organization', 'Issue Date', 'Expiry Date', 'Status'])
    for c in certs:
        writer.writerow([str(c.trainer), c.certification_name, c.issuing_organization, c.issue_date, c.expiry_date, c.status()])
    return response
