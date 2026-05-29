from django.shortcuts import render

def batch_list(request):
    return render(request, 'batch/list.html')

def batch_add(request):
    return render(request, 'batch/add.html')

def batch_detail(request, pk):
    return render(request, 'batch/detail.html')

def batch_edit(request, pk):
    return render(request, 'batch/edit.html')

def batch_delete(request, pk):
    return render(request, 'batch/delete.html')

