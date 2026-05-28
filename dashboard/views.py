from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from trainers.models import Trainer
from skills.models import Skill
from certifications.models import Certification
from django.utils import timezone
from datetime import timedelta


@login_required
def dashboard_view(request):
    today = timezone.now().date()
    total_trainers = Trainer.objects.count()
    active_trainers = Trainer.objects.filter(status__iexact='Active').count()
    available_trainers = Trainer.objects.filter(availability__iexact='Available').count()
    total_skills = Skill.objects.count()
    total_certifications = Certification.objects.count()
    expiring_soon = Certification.objects.filter(expiry_date__isnull=False, expiry_date__lte=today + timedelta(days=30), expiry_date__gte=today).count()

    recent_trainers = Trainer.objects.order_by('-joining_date')[:5]
    latest_certifications = Certification.objects.order_by('-issue_date')[:5]

    # Data for charts
    skills_distribution = Skill.objects.all().values_list('skill_name', flat=True)

    context = {
        'total_trainers': total_trainers,
        'active_trainers': active_trainers,
        'available_trainers': available_trainers,
        'total_skills': total_skills,
        'total_certifications': total_certifications,
        'expiring_soon': expiring_soon,
        'recent_trainers': recent_trainers,
        'latest_certifications': latest_certifications,
        'skills_distribution': list(skills_distribution),
    }
    return render(request, 'dashboard/dashboard.html', context)
