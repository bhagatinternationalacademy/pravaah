from django.db import models
from django.conf import settings

class FutureProposal(models.Model):
    id = models.BigAutoField(primary_key=True)
    """
    Holds the foundational details of any Future Proposal registered in the Pravaah ERP.
    """
    program_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    institute_name = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_proposals'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pravaah_future_proposal'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.program_name} at {self.institute_name}"


class GateZeroForm(models.Model):
    id = models.BigAutoField(primary_key=True)
    """
    Form data for Gate 0 questions:
    - Is training room available?
    - Is hostel facility available?
    - Is trainer available?
    - Is proposal financially feasible?
    """
    YES_NO_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]

    proposal = models.OneToOneField(
        FutureProposal, 
        on_delete=models.CASCADE, 
        related_name='gate_zero'
    )
    is_training_room_available = models.CharField(
        max_length=10, 
        choices=YES_NO_CHOICES, 
        default='No'
    )
    is_hostel_facility_available = models.CharField(
        max_length=10, 
        choices=YES_NO_CHOICES, 
        default='No'
    )
    is_trainer_available = models.CharField(
        max_length=10, 
        choices=YES_NO_CHOICES, 
        default='No'
    )
    is_proposal_financially_feasible = models.CharField(
        max_length=10, 
        choices=YES_NO_CHOICES, 
        default='No'
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pravaah_gate_zero'

    def __str__(self):
        return f"Gate 0 Check for {self.proposal.program_name}"


class GateApprovalForm(models.Model):
    id = models.BigAutoField(primary_key=True)
    """
    Gate Approvals form tracking all 9 activity checkpoints matching the images.
    Once submitted, status becomes 'Pending Marketing Approval' and is routed to the Marketing Person.
    """
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending Marketing Approval', 'Pending Marketing Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    proposal = models.OneToOneField(
        FutureProposal, 
        on_delete=models.CASCADE, 
        related_name='gate_approval'
    )
    
    # 1. Name Of Client & Training Details
    name_of_client = models.CharField(max_length=255, blank=True, null=True)
    mt_course_registration = models.CharField(max_length=255, blank=True, null=True)
    number_of_participants = models.IntegerField(default=0)
    training_type_online_offline = models.CharField(max_length=255, blank=True, null=True)
    
    # 2. Training Need Identification
    training_need_type = models.TextField(blank=True, null=True)
    training_need_content = models.TextField(blank=True, null=True)
    
    # 3. Preparation Of Technical Proposal
    prep_sta_infra = models.TextField(blank=True, null=True)
    prep_consumables = models.TextField(blank=True, null=True)
    prep_ctea_infra = models.TextField(blank=True, null=True)
    prep_mt_availability = models.TextField(blank=True, null=True)
    prep_material = models.TextField(blank=True, null=True)
    prep_material_ppt = models.TextField(blank=True, null=True)
    prep_feedback = models.TextField(blank=True, null=True)
    
    # 4. Session Plan & Coverage
    session_plan_availability = models.TextField(blank=True, null=True)
    
    # 5. Value Addition
    value_addition = models.TextField(blank=True, null=True)
    
    # 6. Assessments, Certification
    assessment_formative = models.TextField(blank=True, null=True)
    assessment_summative = models.TextField(blank=True, null=True)
    assessment_certification = models.TextField(blank=True, null=True)
    assessment_assessors = models.TextField(blank=True, null=True)
    
    # 7. Invoicing
    invoicing_documents = models.TextField(blank=True, null=True)
    
    # 8. Professional Fees
    fees_standard_deviations = models.TextField(blank=True, null=True)
    
    # 9. Challenges & Mitigation Plan
    challenges_mitigation = models.TextField(blank=True, null=True)
    
    # Review & Routing workflow attributes
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES, 
        default='Pending Marketing Approval'
    )
    marketing_remarks = models.TextField(blank=True, null=True)
    
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='submitted_gate_approvals'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_gate_approvals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pravaah_gate_approval'

    def __str__(self):
        return f"Gate Approval for {self.proposal.program_name} (Status: {self.status})"
