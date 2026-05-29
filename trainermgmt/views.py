from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import Trainer, TrainerPayment
from usermgmt.models import AuditLog
from commonservices.utils import get_client_ip

@login_required
def accounts_dashboard_view(request):
    trainers = Trainer.objects.all()
    payments = TrainerPayment.objects.all()
    
    total_paid = payments.filter(status='Completed').aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0.00
    total_pending = payments.filter(status='Pending').aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0.00
    total_failed = payments.filter(status='Failed').aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0.00
    
    # Enrich trainers with paid details
    for t in trainers:
        t.total_paid = t.payments.filter(status='Completed').aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0.00
        t.total_hours = t.payments.filter(status='Completed').aggregate(models.Sum('hours_billed'))['hours_billed__sum'] or 0
        t.pending_count = t.payments.filter(status='Pending').count()
        t.payment_status = 'Fully Paid' if t.total_paid > 0 else 'No Payments'
        if t.pending_count > 0:
            t.payment_status = 'Pending Processing'

    context = {
        'trainers': trainers,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_failed': total_failed,
        'total_trainers': trainers.count()
    }
    return render(request, 'trainermgmt/accounts_dashboard.html', context)


@login_required
def process_payment_view(request, trainer_id):
    trainer = get_object_or_404(Trainer, trainer_id=trainer_id)
    
    if request.method == 'POST':
        amount_paid = request.POST.get('amount_paid')
        payment_mode = request.POST.get('payment_mode')
        reference_number = request.POST.get('reference_number')
        hours_billed = request.POST.get('hours_billed')
        status = request.POST.get('status', 'Completed')
        remarks = request.POST.get('remarks', '')
        
        if not amount_paid or not reference_number:
            messages.error(request, "Amount Paid and Reference Number/Transaction ID are required!")
            return redirect('trainermgmt:process_payment', trainer_id=trainer_id)
            
        try:
            payment = TrainerPayment.objects.create(
                trainer=trainer,
                amount_paid=amount_paid,
                payment_mode=payment_mode,
                reference_number=reference_number,
                hours_billed=hours_billed or 0,
                status=status,
                remarks=remarks
            )
            
            # Log successful action to audit logs
            AuditLog.objects.create(
                user=request.user,
                action=f"Processed Trainer Payment: {trainer.full_name} - Amount: {amount_paid} ({status})",
                module="trainermgmt",
                ip_address=get_client_ip(request),
                browser_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Successfully processed payment of {amount_paid} for {trainer.full_name}!")
            return redirect('trainermgmt:accounts_dashboard')
        except Exception as e:
            messages.error(request, f"Failed to record payment transaction: {e}")
            return redirect('trainermgmt:process_payment', trainer_id=trainer_id)
            
    # Calculate pre-filled values
    default_rate = trainer.hourly_rate
    default_hours = 10
    suggested_amount = default_rate * default_hours
    
    context = {
        'trainer': trainer,
        'suggested_amount': suggested_amount,
        'default_hours': default_hours,
        'default_rate': default_rate
    }
    return render(request, 'trainermgmt/process_payment.html', context)


@login_required
def payment_history_view(request):
    payments = TrainerPayment.objects.all().order_by('-payment_date')
    search = request.GET.get('search')
    
    if search:
        payments = payments.filter(
            models.Q(trainer__first_name__icontains=search) |
            models.Q(trainer__last_name__icontains=search) |
            models.Q(reference_number__icontains=search) |
            models.Q(payment_mode__icontains=search)
        )
        
    context = {
        'payments': payments,
        'search': search
    }
    return render(request, 'trainermgmt/payment_history.html', context)
