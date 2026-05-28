from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Trainer
from django.contrib.auth.decorators import login_required
from .forms import TrainerForm, TrainerRegistrationForm, TrainerProfileEditForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.urls import reverse
from accounts.decorators import trainer_required


@login_required
@staff_member_required
def trainer_list(request):
    q = request.GET.get('q', '').strip()
    qualification = request.GET.get('qualification', '').strip()
    skill = request.GET.get('skill', '').strip()
    availability = request.GET.get('availability', '').strip()
    status = request.GET.get('status', '').strip()
    joining_from = request.GET.get('joining_from', '').strip()
    joining_to = request.GET.get('joining_to', '').strip()

    trainers = Trainer.objects.all().order_by('-joining_date')
    if q:
        trainers = trainers.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(trainer_code__icontains=q)
        )
    if qualification:
        trainers = trainers.filter(qualification__icontains=qualification)
    if skill:
        trainers = trainers.filter(trainerskill__skill_id=skill)
    if availability:
        trainers = trainers.filter(availability=availability)
    if status:
        trainers = trainers.filter(status=status)
    if joining_from:
        trainers = trainers.filter(joining_date__gte=joining_from)
    if joining_to:
        trainers = trainers.filter(joining_date__lte=joining_to)

    trainers = trainers.distinct()

    # Pagination
    from django.core.paginator import Paginator
    import urllib.parse
    paginator = Paginator(trainers, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # build querystring without page
    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    querystring = params.urlencode()

    # skill options
    from skills.models import Skill
    skills = Skill.objects.all()

    context = {
        'trainers': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'querystring': querystring,
        'skills_list': skills,
    }
    return render(request, 'trainers/trainer_list.html', context)


@login_required
@staff_member_required
def trainer_add(request):
    if request.method == 'POST':
        form = TrainerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('trainers:list')
    else:
        form = TrainerForm()
    return render(request, 'trainers/trainer_add.html', {'form': form})


@login_required
def trainer_detail(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)

    # authorization: allow staff or the trainer themselves
    user = request.user
    if not user.is_staff:
        is_owner = False
        try:
            if hasattr(user, 'trainer_profile') and user.trainer_profile and user.trainer_profile.pk == trainer.pk:
                is_owner = True
        except Exception:
            is_owner = False
        if not is_owner and user.email and trainer.email and user.email.lower() != trainer.email.lower():
            from django.contrib import messages
            messages.error(request, 'You do not have permission to view this trainer.')
            return redirect('dashboard:home')

    # fetch trainer skills with related skill object
    skills_qs = trainer.trainerskill_set.select_related('skill').all()
    skills = []
    for ts in skills_qs:
        skills.append({
            'name': ts.skill.skill_name,
            'proficiency': ts.proficiency_level,
        })

    certs_qs = trainer.certification_set.all().order_by('-issue_date')
    certifications = []
    for c in certs_qs:
        certifications.append({
            'id': c.pk,
            'name': c.certification_name,
            'org': c.issuing_organization,
            'issue_date': c.issue_date,
            'expiry_date': c.expiry_date,
            'file_url': c.certificate_file.url if c.certificate_file else None,
            'status': c.status(),
        })

    return render(request, 'trainers/trainer_detail.html', {'trainer': trainer, 'skills': skills, 'certifications': certifications})


@login_required
@trainer_required
def trainer_profile(request):
    # profile for logged-in trainer user
    user = request.user
    trainer = None
    if hasattr(user, 'trainer_profile'):
        trainer = user.trainer_profile
    else:
        # attempt to find trainer by email
        try:
            trainer = Trainer.objects.filter(email__iexact=user.email).first()
        except Exception:
            trainer = None
    if not trainer:
        return render(request, 'trainers/trainer_profile.html', {'trainer': None})

    skills_qs = trainer.trainerskill_set.select_related('skill').all()
    certifications = trainer.certification_set.all().order_by('-issue_date')

    return render(request, 'trainers/trainer_profile.html', {'trainer': trainer, 'skills_qs': skills_qs, 'certifications': certifications})


@login_required
@trainer_required
def trainer_profile_edit(request):
    # allow logged-in trainer to edit limited fields
    user = request.user
    trainer = None
    if hasattr(user, 'trainer_profile'):
        trainer = user.trainer_profile
    else:
        trainer = Trainer.objects.filter(email__iexact=user.email).first()

    if not trainer:
        messages.error(request, 'No trainer profile linked to your account.')
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = TrainerProfileEditForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('trainers:profile')
    else:
        form = TrainerProfileEditForm(instance=trainer)
    return render(request, 'trainers/trainer_profile_edit.html', {'form': form, 'trainer': trainer})


# Registration and admin approval workflow
def trainer_register(request):
    if request.method == 'POST':
        form = TrainerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            trainer = form.save(commit=False)
            trainer.status = 'Pending'
            trainer.save()
            messages.success(request, 'Registration submitted. Admin will review and approve.')
            return redirect('trainers:registration_submitted')
    else:
        form = TrainerRegistrationForm()
    return render(request, 'trainers/trainer_register.html', {'form': form})


def registration_submitted(request):
    return render(request, 'trainers/registration_submitted.html')


@staff_member_required
def pending_trainers(request):
    pending = Trainer.objects.filter(status='Pending').order_by('-id')
    return render(request, 'trainers/pending_trainers.html', {'pending': pending})


@staff_member_required
def approve_trainer(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    if trainer.status != 'Pending':
        messages.warning(request, 'Trainer is not pending.')
        return redirect('trainers:pending_list')

    # create a Django user for the trainer
    base_username = trainer.trainer_code or (trainer.email.split('@')[0] if trainer.email else 'trainer')
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    temp_password = get_random_string(10)
    user = User.objects.create_user(username=username, email=trainer.email)
    user.set_password(temp_password)
    user.is_active = True
    user.is_staff = False
    user.save()

    # assign Trainer group
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    group, created = Group.objects.get_or_create(name='Trainer')

    # set explicit permissions for Trainer group: allow viewing trainers/skills/certifications and limited change_trainer
    perms_to_add = []
    try:
        from trainers.models import Trainer as TrainerModel
        ct_tr = ContentType.objects.get_for_model(TrainerModel)
        for codename in ['view_trainer', 'change_trainer']:
            try:
                perms_to_add.append(Permission.objects.get(codename=codename, content_type=ct_tr))
            except Permission.DoesNotExist:
                pass
    except Exception:
        pass

    try:
        from skills.models import Skill as SkillModel
        ct_skill = ContentType.objects.get_for_model(SkillModel)
        try:
            perms_to_add.append(Permission.objects.get(codename='view_skill', content_type=ct_skill))
        except Permission.DoesNotExist:
            pass
    except Exception:
        pass

    try:
        from certifications.models import Certification as CertificationModel
        ct_cert = ContentType.objects.get_for_model(CertificationModel)
        try:
            perms_to_add.append(Permission.objects.get(codename='view_certification', content_type=ct_cert))
        except Permission.DoesNotExist:
            pass
    except Exception:
        pass

    if perms_to_add:
        group.permissions.add(*perms_to_add)

    user.groups.add(group)

    # link and activate trainer
    trainer.user = user
    trainer.status = 'Active'
    trainer.save()

    # ensure userprofile exists and mark must_change_password
    try:
        up = user.userprofile
        up.must_change_password = True
        up.save()
    except Exception:
        # create if model not present or relation missing
        from accounts.models import UserProfile
        UserProfile.objects.create(user=user, must_change_password=True)

    messages.success(request, f'Trainer approved. Account created for username: {user.username} and temporary password: {temp_password}')
    return redirect('trainers:pending_list')


@staff_member_required
def reject_trainer(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    if trainer.status != 'Pending':
        messages.warning(request, 'Trainer is not pending.')
        return redirect('trainers:pending_list')
    trainer.status = 'Rejected'
    trainer.save()
    messages.info(request, 'Trainer registration rejected.')
    return redirect('trainers:pending_list')


@login_required
@staff_member_required
def trainer_edit(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    if request.method == 'POST':
        form = TrainerForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            form.save()
            return redirect('trainers:detail', pk=trainer.pk)
    else:
        form = TrainerForm(instance=trainer)
    return render(request, 'trainers/trainer_edit.html', {'trainer': trainer, 'form': form})


@login_required
@staff_member_required
def trainer_delete(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    if request.method == 'POST':
        trainer.delete()
        return redirect('trainers:list')
    return render(request, 'trainers/trainer_delete.html', {'trainer': trainer})
