"""
Views for the Billing Management module.

Implements the full bill lifecycle:
  1. Trainers upload bills.
  2. Accounts department reviews, approves, or rejects.
  3. Trainer Admin performs final review, clears payment, or rejects.
  4. In-app notifications keep all stakeholders informed.

Every view is protected by role-based decorators defined in
``billingmgmt.decorators``.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import accounts_required, trainer_admin_required, trainer_required
from .forms import BillUploadForm, RemarkForm
from .models import Bill, BillHistory, Notification


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def create_notification(user, title, message):
    """
    Create a single in-app notification for *user*.

    Args:
        user: The ``User`` instance who will receive the notification.
        title: Short headline for the notification.
        message: Full notification body text.
    """
    Notification.objects.create(user=user, title=title, message=message)


def notify_group(group_name, title, message):
    """
    Send an in-app notification to every user in the given Django auth group.

    If the group does not exist the call is silently ignored.

    Args:
        group_name: Name of the Django ``Group``.
        title: Short headline for the notification.
        message: Full notification body text.
    """
    from django.contrib.auth.models import Group

    try:
        group = Group.objects.get(name=group_name)
        for user in group.user_set.all():
            create_notification(user, title, message)
    except Group.DoesNotExist:
        pass


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required(login_url='/accounts/login/')
def dashboard(request):
    """
    Billing module dashboard providing an overview of bills and recent activity.
    """
    total_bills = Bill.objects.count()
    pending_bills = Bill.objects.filter(current_status__in=['SUBMITTED', 'UNDER_ACCOUNTS_REVIEW', 'APPROVED_BY_ACCOUNTS', 'UNDER_TRAINER_ADMIN_REVIEW']).count()
    cleared_bills = Bill.objects.filter(current_status='PAYMENT_CLEARED').count()
    rejected_bills = Bill.objects.filter(current_status__in=['REJECTED_BY_ACCOUNTS', 'REJECTED_BY_TRAINER_ADMIN']).count()
    
    total_cleared_amount = Bill.objects.filter(current_status='PAYMENT_CLEARED').aggregate(total=Sum('bill_amount'))['total'] or 0
    
    recent_history = BillHistory.objects.select_related('bill', 'action_by').order_by('-timestamp')[:8]
    
    context = {
        'total_bills': total_bills,
        'pending_bills': pending_bills,
        'cleared_bills': cleared_bills,
        'rejected_bills': rejected_bills,
        'total_cleared_amount': total_cleared_amount,
        'recent_history': recent_history,
    }
    return render(request, 'billingmgmt/dashboard.html', context)

# ---------------------------------------------------------------------------
# Trainer views
# ---------------------------------------------------------------------------

@trainer_required
def upload_bill(request):
    """
    Allow a trainer to upload a new bill.

    **GET**: Render an empty ``BillUploadForm``.
    **POST**: Validate and save the bill, create the initial history entry,
    notify the trainer and the Accounts group, then redirect to the
    trainer's bill list.
    """
    if request.method == 'POST':
        form = BillUploadForm(request.POST, request.FILES)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.trainer = request.user
            bill.current_status = 'SUBMITTED'
            bill.save()

            # Audit trail
            BillHistory.objects.create(
                bill=bill,
                action_taken='Bill Submitted',
                action_by=request.user,
                remarks='',
            )

            # Notify the trainer
            create_notification(
                request.user,
                'Bill Uploaded',
                f'Your bill {bill.bill_number} has been submitted successfully.',
            )

            # Notify the Accounts group
            notify_group(
                'Accounts',
                'New Bill Submitted',
                f'A new bill {bill.bill_number} from '
                f'{request.user.get_full_name() or request.user.username} requires review.',
            )

            messages.success(request, 'Bill uploaded successfully.')
            return redirect('billing:my_bills')
    else:
        form = BillUploadForm()

    return render(request, 'billingmgmt/upload_bill.html', {'form': form})


@trainer_required
def my_bills(request):
    """
    Display all bills belonging to the currently logged-in trainer.
    """
    bills = Bill.objects.filter(trainer=request.user)
    return render(request, 'billingmgmt/my_bills.html', {'bills': bills})


# ---------------------------------------------------------------------------
# Accounts department views
# ---------------------------------------------------------------------------

@accounts_required
def accounts_pending_bills(request):
    """
    List bills that are pending review by the Accounts department.

    Shows bills with status ``SUBMITTED`` or ``UNDER_ACCOUNTS_REVIEW``.
    """
    bills = Bill.objects.filter(
        current_status__in=['SUBMITTED', 'UNDER_ACCOUNTS_REVIEW']
    )
    remark_form = RemarkForm()
    return render(
        request,
        'billingmgmt/accounts_pending_bills.html',
        {'bills': bills, 'remark_form': remark_form},
    )


@accounts_required
def accounts_approve_bill(request, pk):
    """
    Approve a bill on behalf of the Accounts department.

    Sets the bill status to ``APPROVED_BY_ACCOUNTS``, logs the action,
    and notifies the trainer and TrainerAdmin group.
    """
    if request.method != 'POST':
        return redirect('billing:accounts_pending')

    bill = get_object_or_404(Bill, pk=pk)

    bill.current_status = 'APPROVED_BY_ACCOUNTS'
    bill.remarks = ''
    bill.save()

    BillHistory.objects.create(
        bill=bill,
        action_taken='Approved by Accounts Department',
        action_by=request.user,
        remarks='',
    )

    # Notify the trainer
    create_notification(
        bill.trainer,
        'Bill Approved by Accounts',
        f'Your bill {bill.bill_number} has been approved by the Accounts department.',
    )

    # Notify TrainerAdmin group
    notify_group(
        'TrainerAdmin',
        'Bill Pending Approval',
        f'Bill {bill.bill_number} has been approved by Accounts and awaits your review.',
    )

    messages.success(request, f'Bill {bill.bill_number} approved successfully.')
    return redirect('billing:accounts_pending')


@accounts_required
def accounts_reject_bill(request, pk):
    """
    Reject a bill on behalf of the Accounts department.

    Requires remarks explaining the reason for rejection. Notifies the
    trainer of the rejection along with the reviewer's remarks.
    """
    if request.method != 'POST':
        return redirect('billing:accounts_pending')

    bill = get_object_or_404(Bill, pk=pk)
    form = RemarkForm(request.POST)

    if form.is_valid():
        bill.current_status = 'REJECTED_BY_ACCOUNTS'
        bill.remarks = form.cleaned_data['remarks']
        bill.save()

        BillHistory.objects.create(
            bill=bill,
            action_taken='Rejected by Accounts Department',
            action_by=request.user,
            remarks=form.cleaned_data['remarks'],
        )

        create_notification(
            bill.trainer,
            'Bill Rejected by Accounts',
            f'Your bill {bill.bill_number} has been rejected by the Accounts department. '
            f'Remarks: {form.cleaned_data["remarks"]}',
        )

        messages.warning(request, f'Bill {bill.bill_number} has been rejected.')
    else:
        messages.error(request, 'Please provide valid remarks for rejection.')

    return redirect('billing:accounts_pending')


# ---------------------------------------------------------------------------
# Trainer Admin views
# ---------------------------------------------------------------------------

@trainer_admin_required
def trainer_admin_bills(request):
    """
    List bills awaiting Trainer Admin review.

    Shows bills with status ``APPROVED_BY_ACCOUNTS``.
    """
    bills = Bill.objects.filter(current_status='APPROVED_BY_ACCOUNTS')
    remark_form = RemarkForm()
    return render(
        request,
        'billingmgmt/trainer_admin_bills.html',
        {'bills': bills, 'remark_form': remark_form},
    )


@trainer_admin_required
def trainer_admin_approve_bill(request, pk):
    """
    Clear payment for a bill on behalf of the Trainer Admin.

    Sets the bill status to ``PAYMENT_CLEARED``, records the
    ``final_approved_at`` timestamp, and notifies the trainer.
    """
    if request.method != 'POST':
        return redirect('billing:trainer_admin_bills')

    bill = get_object_or_404(Bill, pk=pk)

    bill.current_status = 'PAYMENT_CLEARED'
    bill.final_approved_at = timezone.now()
    bill.remarks = ''
    bill.save()

    BillHistory.objects.create(
        bill=bill,
        action_taken='Payment Cleared by Trainer Admin',
        action_by=request.user,
        remarks='',
    )

    create_notification(
        bill.trainer,
        'Payment Cleared',
        f'Payment for your bill {bill.bill_number} has been cleared by Trainer Admin.',
    )

    messages.success(request, f'Payment for bill {bill.bill_number} cleared successfully.')
    return redirect('billing:trainer_admin_bills')


@trainer_admin_required
def trainer_admin_reject_bill(request, pk):
    """
    Reject a bill on behalf of the Trainer Admin.

    Requires remarks explaining the reason for rejection. Notifies the
    trainer of the rejection along with the reviewer's remarks.
    """
    if request.method != 'POST':
        return redirect('billing:trainer_admin_bills')

    bill = get_object_or_404(Bill, pk=pk)
    form = RemarkForm(request.POST)

    if form.is_valid():
        bill.current_status = 'REJECTED_BY_TRAINER_ADMIN'
        bill.remarks = form.cleaned_data['remarks']
        bill.save()

        BillHistory.objects.create(
            bill=bill,
            action_taken='Rejected by Trainer Admin',
            action_by=request.user,
            remarks=form.cleaned_data['remarks'],
        )

        create_notification(
            bill.trainer,
            'Bill Rejected by Trainer Admin',
            f'Your bill {bill.bill_number} has been rejected by Trainer Admin. '
            f'Remarks: {form.cleaned_data["remarks"]}',
        )

        messages.warning(request, f'Bill {bill.bill_number} has been rejected.')
    else:
        messages.error(request, 'Please provide valid remarks for rejection.')

    return redirect('billing:trainer_admin_bills')


# ---------------------------------------------------------------------------
# Notification views
# ---------------------------------------------------------------------------

@login_required(login_url='/accounts/login/')
def notifications_view(request):
    """Display all notifications for the currently logged-in user."""
    notifications = Notification.objects.filter(user=request.user)
    return render(
        request,
        'billingmgmt/notifications.html',
        {'notifications': notifications},
    )


@login_required(login_url='/accounts/login/')
def mark_notification_read(request, pk):
    """Mark a single notification as read."""
    if request.method != 'POST':
        return redirect('billing:notifications')

    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('billing:notifications')


@login_required(login_url='/accounts/login/')
def mark_all_notifications_read(request):
    """Mark all unread notifications for the current user as read."""
    if request.method != 'POST':
        return redirect('billing:notifications')

    request.user.billing_notifications.filter(is_read=False).update(is_read=True)
    return redirect('billing:notifications')


# ---------------------------------------------------------------------------
# Bill PDF preview
# ---------------------------------------------------------------------------

@login_required(login_url='/accounts/login/')
def bill_pdf_preview(request, pk):
    """
    Render a preview page for a bill's uploaded PDF.

    Access control:
      - Trainers can only preview their own bills.
      - Accounts and TrainerAdmin users can preview any bill.
      - Superusers can preview any bill.
    """
    bill = get_object_or_404(Bill, pk=pk)

    # Determine the user's groups.
    user_groups = set(request.user.groups.values_list('name', flat=True))

    # Access control check.
    if not request.user.is_superuser:
        is_owner = bill.trainer == request.user
        is_reviewer = bool(user_groups.intersection({'Accounts', 'TrainerAdmin'}))
        if not (is_owner or is_reviewer):
            return HttpResponseForbidden(
                '<h3 style="text-align:center;margin-top:50px;">'
                '⛔ Access Denied. You do not have permission to view this bill.</h3>'
            )

    return render(request, 'billingmgmt/bill_pdf_preview.html', {'bill': bill})
