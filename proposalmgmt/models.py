from django.db import models
from django.conf import settings

class FutureProposal(models.Model):
    program_name = models.CharField(max_length=255)
    institute_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_proposals'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.program_name} at {self.institute_name}"

class GateZeroForm(models.Model):
    YES_NO_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]
    proposal = models.OneToOneField(
        FutureProposal,
        on_delete=models.CASCADE,
        related_name='gate_zero'
    )
    is_training_room_available = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='No')
    is_hostel_facility_available = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='No')
    is_trainer_available = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='No')
    is_proposal_financially_feasible = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='No')
    
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_gate_zeros'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gate 0 for {self.proposal.program_name}"

class GateApprovalForm(models.Model):
    STATUS_CHOICES = [
        ('Pending Marketing Approval', 'Pending Marketing Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    proposal = models.OneToOneField(
        FutureProposal,
        on_delete=models.CASCADE,
        related_name='gate_approval'
    )
    
    name_of_client = models.CharField(max_length=255, blank=True)
    mt_course_registration = models.CharField(max_length=255, blank=True)
    number_of_participants = models.IntegerField(default=0)
    training_type_online_offline = models.CharField(max_length=50, blank=True)
    
    training_need_type = models.CharField(max_length=100, blank=True)
    training_need_content = models.TextField(blank=True)
    
    prep_sta_infra = models.CharField(max_length=255, blank=True)
    prep_consumables = models.CharField(max_length=255, blank=True)
    prep_ctea_infra = models.CharField(max_length=255, blank=True)
    prep_mt_availability = models.CharField(max_length=255, blank=True)
    prep_material = models.CharField(max_length=255, blank=True)
    prep_material_ppt = models.CharField(max_length=255, blank=True)
    prep_feedback = models.CharField(max_length=255, blank=True)
    
    session_plan_availability = models.CharField(max_length=255, blank=True)
    value_addition = models.CharField(max_length=255, blank=True)
    
    assessment_formative = models.CharField(max_length=255, blank=True)
    assessment_summative = models.CharField(max_length=255, blank=True)
    assessment_certification = models.CharField(max_length=255, blank=True)
    assessment_assessors = models.CharField(max_length=255, blank=True)
    
    invoicing_documents = models.CharField(max_length=255, blank=True)
    fees_standard_deviations = models.CharField(max_length=255, blank=True)
    challenges_mitigation = models.TextField(blank=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending Marketing Approval')
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

    def __str__(self):
        return f"Gate Approval for {self.proposal.program_name}"
