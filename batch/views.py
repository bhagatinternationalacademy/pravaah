from django.shortcuts import render, get_object_or_404
from .models import Batch


def batch_list(request):
    """List batches from the existing 'batches' table. Shows empty state if none."""
    batches = Batch.objects.order_by('-start_date')
    return render(request, 'batch/list.html', {'batches': batches})


def batch_add(request):
    # Placeholder: creation flow can be added later
    return render(request, 'batch/add.html')


def batch_detail(request, pk):
    """Show details for a single batch. Works even if DB has no rows."""
    batch = get_object_or_404(Batch, pk=pk)
    return render(request, 'batch/detail.html', {'batch': batch})


def batch_edit(request, pk):
    # Placeholder for edit form
    return render(request, 'batch/edit.html')


def batch_delete(request, pk):
    # Placeholder for delete confirmation
    return render(request, 'batch/delete.html')
