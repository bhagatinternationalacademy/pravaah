from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from django.utils import timezone
from django.db.models import Q
from .models import FutureProposal, GateZeroForm, GateApprovalForm

# Helper to check if a user belongs to the 'Marketing' group
def is_marketing(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name='Marketing').exists()

@login_required
def landing_page(request):
    # Ensure the Marketing role is created in the system
    Group.objects.get_or_create(name='Marketing')
    
    # Calculate operational metrics for dashboard tiles
    proposals = FutureProposal.objects.all()
    proposals_count = proposals.count()
    
    gate_zero_completed = GateZeroForm.objects.count()
    
    pending_approvals = GateApprovalForm.objects.filter(status='Pending Marketing Approval')
    gate_approvals_pending = pending_approvals.count()
    
    # Calculate detailed stage metrics across 6 operational pipeline levels
    stage_pipeline_count = FutureProposal.objects.filter(gate_zero__isnull=True).count()
    
    stage_failed_count = GateZeroForm.objects.filter(
        Q(is_training_room_available='No') |
        Q(is_hostel_facility_available='No') |
        Q(is_trainer_available='No') |
        Q(is_proposal_financially_feasible='No')
    ).count()
    
    stage_passed_count = FutureProposal.objects.filter(
        gate_zero__isnull=False,
        gate_zero__is_training_room_available='Yes',
        gate_zero__is_hostel_facility_available='Yes',
        gate_zero__is_trainer_available='Yes',
        gate_zero__is_proposal_financially_feasible='Yes',
        gate_approval__isnull=True
    ).count()
    
    stage_pending_count = pending_approvals.count()
    stage_approved_count = GateApprovalForm.objects.filter(status='Approved').count()
    stage_rejected_count = GateApprovalForm.objects.filter(status='Rejected').count()
    
    is_marketing_user = False
    if request.user.is_authenticated:
        is_marketing_user = is_marketing(request.user)
    
    context = {
        'proposals_count': proposals_count,
        'gate_zero_completed': gate_zero_completed,
        'gate_approvals_pending': gate_approvals_pending,
        'is_marketing_user': is_marketing_user,
        'pending_approvals': pending_approvals if is_marketing_user else None,
        
        # Pass counts for visual pipeline stages
        'stage_pipeline_count': stage_pipeline_count,
        'stage_failed_count': stage_failed_count,
        'stage_passed_count': stage_passed_count,
        'stage_pending_count': stage_pending_count,
        'stage_approved_count': stage_approved_count,
        'stage_rejected_count': stage_rejected_count,
    }
    return render(request, 'landing.html', context)

@login_required
def future_proposals_list(request):
    search_query = request.GET.get('search', '').strip()
    proposals = FutureProposal.objects.all()
    
    if search_query:
        proposals = proposals.filter(
            Q(program_name__icontains=search_query) |
            Q(institute_name__icontains=search_query)
        )
        
    context = {
        'proposals': proposals,
        'search_query': search_query,
    }
    return render(request, 'future_proposals.html', context)

@login_required
def add_proposal(request):
    if request.method == 'POST':
        program_name = request.POST.get('program_name', '').strip()
        institute_name = request.POST.get('institute_name', '').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if not all([program_name, institute_name, start_date, end_date]):
            messages.error(request, "Please fill in all fields to register the proposal.")
            return render(request, 'create_proposal.html')
            
        proposal = FutureProposal.objects.create(
            program_name=program_name,
            institute_name=institute_name,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user if request.user.is_authenticated else None
        )
        messages.success(request, f"Future Proposal '{proposal.program_name}' registered successfully! Let's fill the Gate 0 feasibility check now.")
        return redirect('pravaah_gate_zero_proposal', proposal_id=proposal.id)
        
    return render(request, 'create_proposal.html')

@login_required
def gate_zero_form(request, proposal_id=None):
    selected_proposal = None
    if proposal_id:
        selected_proposal = get_object_or_404(FutureProposal, id=proposal_id)
        
    # Find proposals that DO NOT have a Gate 0 form submitted yet
    eligible_proposals = FutureProposal.objects.filter(gate_zero__isnull=True)
    
    existing_gate_zero = None
    if selected_proposal and hasattr(selected_proposal, 'gate_zero'):
        existing_gate_zero = selected_proposal.gate_zero

    if request.method == 'POST':
        p_id = request.POST.get('proposal_id')
        if not p_id and selected_proposal:
            p_id = selected_proposal.id
            
        if not p_id:
            messages.error(request, "Please select a valid Future Proposal.")
            return redirect('pravaah_gate_zero')
            
        proposal = get_object_or_404(FutureProposal, id=p_id)
        
        is_training_room = request.POST.get('is_training_room_available', 'No')
        is_hostel = request.POST.get('is_hostel_facility_available', 'No')
        is_trainer = request.POST.get('is_trainer_available', 'No')
        is_financial = request.POST.get('is_proposal_financially_feasible', 'No')
        
        # Create or update Gate 0 check-list
        gate_zero, created = GateZeroForm.objects.update_or_create(
            proposal=proposal,
            defaults={
                'is_training_room_available': is_training_room,
                'is_hostel_facility_available': is_hostel,
                'is_trainer_available': is_trainer,
                'is_proposal_financially_feasible': is_financial,
                'submitted_by': request.user if request.user.is_authenticated else None
            }
        )
        
        passed = (is_training_room == 'Yes' and 
                  is_hostel == 'Yes' and 
                  is_trainer == 'Yes' and 
                  is_financial == 'Yes')
        
        if passed:
            messages.success(request, f"Gate 0 check passed for '{proposal.program_name}'! Please fill out the detailed Gate Approvals checksheet now.")
            return redirect('pravaah_gate_approval_proposal', proposal_id=proposal.id)
        else:
            messages.warning(request, f"Gate 0 check submitted for '{proposal.program_name}'. However, the proposal did not pass the feasibility checks because one or more inputs were marked 'No'.")
            return redirect('pravaah_future_proposals')
        
    context = {
        'selected_proposal': selected_proposal,
        'eligible_proposals': eligible_proposals,
        'existing_gate_zero': existing_gate_zero,
    }
    return render(request, 'gate_zero.html', context)

@login_required
def gate_approval_form(request, proposal_id=None):
    selected_proposal = None
    if proposal_id:
        selected_proposal = get_object_or_404(FutureProposal, id=proposal_id)
        # Strict validation: proposal must have a Gate 0 check-list where all 4 questions are YES
        if not (hasattr(selected_proposal, 'gate_zero') and 
                selected_proposal.gate_zero.is_training_room_available == 'Yes' and 
                selected_proposal.gate_zero.is_hostel_facility_available == 'Yes' and 
                selected_proposal.gate_zero.is_trainer_available == 'Yes' and 
                selected_proposal.gate_zero.is_proposal_financially_feasible == 'Yes'):
            messages.error(request, f"Proposal '{selected_proposal.program_name}' cannot enter Gate Approvals because it hasn't passed the Gate 0 feasibility checks.")
            return redirect('pravaah_future_proposals')
        
    # Find proposals that have a Gate 0 form successfully submitted with all YES answers and do NOT have an active Gate Approval yet
    eligible_proposals = FutureProposal.objects.filter(
        gate_zero__isnull=False,
        gate_zero__is_training_room_available='Yes',
        gate_zero__is_hostel_facility_available='Yes',
        gate_zero__is_trainer_available='Yes',
        gate_zero__is_proposal_financially_feasible='Yes',
        gate_approval__isnull=True
    )
    
    # If editing / loading existing approval
    existing_approval = None
    if selected_proposal and hasattr(selected_proposal, 'gate_approval'):
        existing_approval = selected_proposal.gate_approval

    if request.method == 'POST':
        p_id = request.POST.get('proposal_id')
        if not p_id and selected_proposal:
            p_id = selected_proposal.id
            
        if not p_id:
            messages.error(request, "Please select a valid Future Proposal.")
            return redirect('pravaah_gate_approval')
            
        proposal = get_object_or_404(FutureProposal, id=p_id)
        
        # Strict POST check validation
        if not (hasattr(proposal, 'gate_zero') and 
                proposal.gate_zero.is_training_room_available == 'Yes' and 
                proposal.gate_zero.is_hostel_facility_available == 'Yes' and 
                proposal.gate_zero.is_trainer_available == 'Yes' and 
                proposal.gate_zero.is_proposal_financially_feasible == 'Yes'):
            messages.error(request, "Operational Block: Selected proposal must have successfully passed all Gate 0 criteria.")
            return redirect('pravaah_landing')
        
        # Capture form remarks and checkpoints matching the screenshots
        defaults = {
            'name_of_client': request.POST.get('name_of_client', '').strip(),
            'mt_course_registration': request.POST.get('mt_course_registration', '').strip(),
            'number_of_participants': int(request.POST.get('number_of_participants', 0) or 0),
            'training_type_online_offline': request.POST.get('training_type_online_offline', '').strip(),
            
            'training_need_type': request.POST.get('training_need_type', '').strip(),
            'training_need_content': request.POST.get('training_need_content', '').strip(),
            
            'prep_sta_infra': request.POST.get('prep_sta_infra', '').strip(),
            'prep_consumables': request.POST.get('prep_consumables', '').strip(),
            'prep_ctea_infra': request.POST.get('prep_ctea_infra', '').strip(),
            'prep_mt_availability': request.POST.get('prep_mt_availability', '').strip(),
            'prep_material': request.POST.get('prep_material', '').strip(),
            'prep_material_ppt': request.POST.get('prep_material_ppt', '').strip(),
            'prep_feedback': request.POST.get('prep_feedback', '').strip(),
            
            'session_plan_availability': request.POST.get('session_plan_availability', '').strip(),
            'value_addition': request.POST.get('value_addition', '').strip(),
            
            'assessment_formative': request.POST.get('assessment_formative', '').strip(),
            'assessment_summative': request.POST.get('assessment_summative', '').strip(),
            'assessment_certification': request.POST.get('assessment_certification', '').strip(),
            'assessment_assessors': request.POST.get('assessment_assessors', '').strip(),
            
            'invoicing_documents': request.POST.get('invoicing_documents', '').strip(),
            'fees_standard_deviations': request.POST.get('fees_standard_deviations', '').strip(),
            'challenges_mitigation': request.POST.get('challenges_mitigation', '').strip(),
            
            'status': 'Pending Marketing Approval', # Set status to route to Marketing Review
            'submitted_by': request.user if request.user.is_authenticated else None,
            'marketing_remarks': None # Clear any previous rejection remarks
        }
        
        GateApprovalForm.objects.update_or_create(
            proposal=proposal,
            defaults=defaults
        )
        
        messages.success(request, f"Gate Approval Form for '{proposal.program_name}' successfully routed to the Marketing Person.")
        return redirect('pravaah_landing')
        
    context = {
        'selected_proposal': selected_proposal,
        'eligible_proposals': eligible_proposals,
        'existing_approval': existing_approval,
    }
    return render(request, 'gate_approval.html', context)

@login_required
def marketing_queue(request):
    if not is_marketing(request.user):
        messages.error(request, "Access Denied: You do not have the required permissions to view the Marketing Approvals board.")
        return redirect('pravaah_landing')
        
    pending_approvals = GateApprovalForm.objects.filter(status='Pending Marketing Approval')
    completed_approvals = GateApprovalForm.objects.filter(status__in=['Approved', 'Rejected'])
    
    context = {
        'pending_approvals': pending_approvals,
        'completed_approvals': completed_approvals,
    }
    return render(request, 'marketing_queue.html', context)

@login_required
def approve_gate_approval(request, approval_id):
    if not is_marketing(request.user):
        messages.error(request, "Access Denied: You do not have permission to approve proposals.")
        return redirect('pravaah_landing')
        
    approval = get_object_or_404(GateApprovalForm, id=approval_id)
    remarks = request.POST.get('marketing_remarks', '').strip()
    
    approval.status = 'Approved'
    approval.marketing_remarks = remarks or "Approved by Marketing."
    approval.reviewed_by = request.user if request.user.is_authenticated else None
    approval.updated_at = timezone.now()
    approval.save()
    
    messages.success(request, f"Gate Approval for '{approval.proposal.program_name}' has been Approved.")
    return redirect('pravaah_marketing_queue')

@login_required
def reject_gate_approval(request, approval_id):
    if not is_marketing(request.user):
        messages.error(request, "Access Denied: You do not have permission to reject proposals.")
        return redirect('pravaah_landing')
        
    approval = get_object_or_404(GateApprovalForm, id=approval_id)
    remarks = request.POST.get('marketing_remarks', '').strip()
    
    if not remarks:
        messages.error(request, "Rejection Remarks are required when rejecting a proposal.")
        # Redirect back to the detail page or queue
        return redirect('pravaah_marketing_queue')
        
    approval.status = 'Rejected'
    approval.marketing_remarks = remarks
    approval.reviewed_by = request.user if request.user.is_authenticated else None
    approval.updated_at = timezone.now()
    approval.save()
    
    messages.warning(request, f"Gate Approval for '{approval.proposal.program_name}' has been Rejected.")
    return redirect('pravaah_marketing_queue')
