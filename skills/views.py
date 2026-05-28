from django.shortcuts import render, redirect
from .models import Skill, TrainerSkill
from trainers.models import Trainer
from django.contrib.auth.decorators import login_required
from .forms import SkillForm, AssignSkillForm


@login_required
def skill_list(request):
    skills = Skill.objects.all()
    return render(request, 'skills/skill_list.html', {'skills': skills})


@login_required
def skill_add(request):
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('skills:list')
    else:
        form = SkillForm()
    return render(request, 'skills/skill_add.html', {'form': form})


@login_required
def assign_skill(request):
    if request.method == 'POST':
        form = AssignSkillForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('skills:list')
    else:
        form = AssignSkillForm()
    return render(request, 'skills/assign_skill.html', {'form': form})
