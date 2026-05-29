from django.shortcuts import render, redirect
from .models import Assessment
from .forms import AssessmentForm


def assessment_list(request):

    assessments = Assessment.objects.all()

    context = {
        'assessments': assessments
    }

    return render(
        request,
        'assessment/list.html',
        context
    )


def create_assessment(request):

    if request.method == 'POST':

        form = AssessmentForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect('assessment_list')

    else:

        form = AssessmentForm()

    context = {
        'form': form
    }

    return render(
        request,
        'assessment/create.html',
        context
    )


def edit_assessment(request, id):
    assessment = Assessment.objects.get(id=id)

    if request.method == 'POST':

        form = AssessmentForm(
            request.POST,
            instance=assessment
        )

        if form.is_valid():

            form.save()

            return redirect('assessment_list')

    else:

        form = AssessmentForm(
            instance=assessment
        )

    context = {
        'form': form
    }

    return render(
        request,
        'assessment/edit.html',
        context
    )


def delete_assessment(request, id):

    assessment = Assessment.objects.get(id=id)

    assessment.delete()

    return redirect('assessment_list')