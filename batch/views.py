from django.shortcuts import render

def batch_list(request):
    return render(request, 'batch/list.html')

def batch_add(request):
    return render(request, 'batch/add.html')

from django.shortcuts import get_object_or_404
from .models import BatchAssignment


def batch_detail(request, pk):
    # show batch details and actions like attendance history
    batch = get_object_or_404(BatchAssignment, pk=pk)
    return render(request, 'batch/detail.html', {'batch': batch})

def batch_edit(request, pk):
    return render(request, 'batch/edit.html')

def batch_delete(request, pk):
    return render(request, 'batch/delete.html')

