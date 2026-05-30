import os
import django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Ensure standard groups exist
trainer_group, _ = Group.objects.get_or_create(name='Trainer')
accounts_group, _ = Group.objects.get_or_create(name='Accounts')
trainer_admin_group, _ = Group.objects.get_or_create(name='TrainerAdmin')
marketing_group, _ = Group.objects.get_or_create(name='Marketing')

# Helper to create/update users
def get_or_create_user(username, email, password, group_name=None, is_staff=False, is_superuser=False):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_staff': is_staff,
            'is_superuser': is_superuser,
            'is_email_verified': True
        }
    )
    user.set_password(password)
    user.is_email_verified = True
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.save()
    if group_name:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
    return user

# Create specific personas
trainer_user = get_or_create_user('trainer1', 'trainer1@pravaah.edu', 'Guru@om459', 'Trainer')
accounts_user = get_or_create_user('accounts1', 'accounts1@pravaah.edu', 'Guru@om459', 'Accounts')
trainer_admin_user = get_or_create_user('traineradmin1', 'traineradmin1@pravaah.edu', 'Guru@om459', 'TrainerAdmin')
marketing_user = get_or_create_user('marketing1', 'marketing1@pravaah.edu', 'Guru@om459', 'Marketing')
superuser = get_or_create_user('harshada2576', 'harshada2576@gmail.com', 'Guru@om459', 'Marketing', is_staff=True, is_superuser=True)

# Clean existing data to avoid conflicts (while keeping users)
from proposalmgmt.models import FutureProposal, GateZeroForm, GateApprovalForm
from billingmgmt.models import Bill, BillHistory, Notification

# Delete existing records to start with clean and beautiful dummy data
GateApprovalForm.objects.all().delete()
GateZeroForm.objects.all().delete()
FutureProposal.objects.all().delete()
BillHistory.objects.all().delete()
Bill.objects.all().delete()
Notification.objects.all().delete()

# --- PROPOSAL WORKFLOW CASES ---

# Case A: A raw proposal in the pipeline (has no Gate 0 yet)
proposal_a = FutureProposal.objects.create(
    program_name='Advanced Machine Learning & Neural Networks',
    institute_name='IIT Bombay - Tech Hub',
    start_date=timezone.now().date() + timedelta(days=30),
    end_date=timezone.now().date() + timedelta(days=35),
    created_by=superuser
)

# Case B: A proposal that failed Gate 0 feasibility check (at least one 'No')
proposal_b = FutureProposal.objects.create(
    program_name='Cybersecurity Incident Response Bootcamp',
    institute_name='COEP Technological University',
    start_date=timezone.now().date() + timedelta(days=45),
    end_date=timezone.now().date() + timedelta(days=50),
    created_by=superuser
)
GateZeroForm.objects.create(
    proposal=proposal_b,
    is_training_room_available='Yes',
    is_hostel_facility_available='No',  # Fails feasibility
    is_trainer_available='Yes',
    is_proposal_financially_feasible='No',  # Fails feasibility
    submitted_by=superuser
)

# Case C: A proposal that passed Gate 0 feasibility (all 'Yes'), but has no Gate Approval submitted yet
proposal_c = FutureProposal.objects.create(
    program_name='Cloud Architecture & DevOps Masterclass',
    institute_name='VJTI Mumbai - Center of Excellence',
    start_date=timezone.now().date() + timedelta(days=15),
    end_date=timezone.now().date() + timedelta(days=20),
    created_by=superuser
)
GateZeroForm.objects.create(
    proposal=proposal_c,
    is_training_room_available='Yes',
    is_hostel_facility_available='Yes',
    is_trainer_available='Yes',
    is_proposal_financially_feasible='Yes',
    submitted_by=superuser
)

# Case D: A proposal that passed Gate 0, has Gate Approval submitted and is awaiting Marketing review ('Pending Marketing Approval')
proposal_d = FutureProposal.objects.create(
    program_name='Full-Stack Software Engineering Accelerator',
    institute_name='BMS College of Engineering',
    start_date=timezone.now().date() + timedelta(days=60),
    end_date=timezone.now().date() + timedelta(days=65),
    created_by=superuser
)
GateZeroForm.objects.create(
    proposal=proposal_d,
    is_training_room_available='Yes',
    is_hostel_facility_available='Yes',
    is_trainer_available='Yes',
    is_proposal_financially_feasible='Yes',
    submitted_by=superuser
)
GateApprovalForm.objects.create(
    proposal=proposal_d,
    name_of_client='TechCorp Solutions Inc.',
    mt_course_registration='MT-ENG-2026-FSD',
    number_of_participants=45,
    training_type_online_offline='Offline',
    training_need_type='Technical Skills Alignment',
    training_need_content='Equip engineering grads with production-grade Django, React and cloud deployment skills.',
    prep_sta_infra='Available - Room 402 Lab fully equipped',
    prep_consumables='Ordered - Notepad, pens and markers set',
    prep_ctea_infra='Configured - Coffee and tea lounge booking',
    prep_mt_availability='Confirmed - Master trainer available',
    prep_material='Ready - Handbook and digital notes printed',
    prep_material_ppt='Ready - Slides and deck verified',
    prep_feedback='Configured - QR feedback portal active',
    session_plan_availability='Yes - 5 day hour-by-hour breakdown',
    value_addition='Includes capstone project and interview prep',
    assessment_formative='Yes - Daily laboratory challenges',
    assessment_summative='Yes - End-of-course online exam',
    assessment_certification='Yes - Jointly signed institutional certificate',
    assessment_assessors='Internal - Panel of senior tech architects',
    invoicing_documents='Approved - PO #TC-9923 received',
    fees_standard_deviations='None - Standard corporate rate applied',
    challenges_mitigation='Challenge: Internet load. Mitigation: Local offline mirror configured.',
    status='Pending Marketing Approval',
    submitted_by=superuser
)

# Case E: A proposal that passed Gate 0, Gate Approval was submitted, but was Rejected by Marketing
proposal_e = FutureProposal.objects.create(
    program_name='Blockchain & Smart Contracts Specialization',
    institute_name='RV College of Engineering',
    start_date=timezone.now().date() + timedelta(days=75),
    end_date=timezone.now().date() + timedelta(days=80),
    created_by=superuser
)
GateZeroForm.objects.create(
    proposal=proposal_e,
    is_training_room_available='Yes',
    is_hostel_facility_available='Yes',
    is_trainer_available='Yes',
    is_proposal_financially_feasible='Yes',
    submitted_by=superuser
)
GateApprovalForm.objects.create(
    proposal=proposal_e,
    name_of_client='Decentralized Labs LLC',
    mt_course_registration='MT-CRYPTO-404',
    number_of_participants=20,
    training_type_online_offline='Online',
    training_need_type='Cryptographic Engineering',
    training_need_content='Build production smart contracts on EVM compatible chains.',
    prep_sta_infra='N/A - Fully virtual course via Zoom',
    prep_consumables='None - Digital resources only',
    prep_ctea_infra='N/A',
    prep_mt_availability='Confirmed',
    prep_material='In Progress - Draft module needs review',
    prep_material_ppt='In Progress',
    prep_feedback='Configured',
    session_plan_availability='No - Needs curriculum outline',
    value_addition='Dapp audit checklist integration',
    assessment_formative='Yes',
    assessment_summative='Yes',
    assessment_certification='Yes',
    assessment_assessors='External - Blockchain Audit Guild',
    invoicing_documents='Pending - Client PO not yet issued',
    fees_standard_deviations='Deviated - 20% discount granted',
    challenges_mitigation='Challenge: Node failure. Mitigation: Infura backup.',
    status='Rejected',
    marketing_remarks='Please clarify the session plan and attach the updated curriculum outline. The invoicing documents are still pending and must be signed by the client before gate approval.',
    submitted_by=superuser,
    reviewed_by=marketing_user
)

# Case F: A proposal that is fully approved through Gate 0 and Marketing ('Approved')
proposal_f = FutureProposal.objects.create(
    program_name='Artificial Intelligence & Big Data Analytics',
    institute_name='IIT Madras - Research Park',
    start_date=timezone.now().date() + timedelta(days=90),
    end_date=timezone.now().date() + timedelta(days=95),
    created_by=superuser
)
GateZeroForm.objects.create(
    proposal=proposal_f,
    is_training_room_available='Yes',
    is_hostel_facility_available='Yes',
    is_trainer_available='Yes',
    is_proposal_financially_feasible='Yes',
    submitted_by=superuser
)
GateApprovalForm.objects.create(
    proposal=proposal_f,
    name_of_client='National Analytics Council',
    mt_course_registration='MT-AI-2026-N',
    number_of_participants=80,
    training_type_online_offline='Offline',
    training_need_type='National Capability Build',
    training_need_content='Train institutional leaders in AI ethics, model evaluation, and LLM fine-tuning pipelines.',
    prep_sta_infra='Available - Seminar Auditorium A',
    prep_consumables='Available',
    prep_ctea_infra='Available - Catering contract approved',
    prep_mt_availability='Confirmed',
    prep_material='Ready',
    prep_material_ppt='Ready',
    prep_feedback='Ready',
    session_plan_availability='Yes - Fully documented',
    value_addition='Includes hand-on fine-tuning labs on GPU cluster',
    assessment_formative='Yes',
    assessment_summative='Yes',
    assessment_certification='Yes',
    assessment_assessors='Panel of AI researchers',
    invoicing_documents='Signed and processed',
    fees_standard_deviations='None',
    challenges_mitigation='Challenge: Compute limit. Mitigation: Dedicated cloud GPUs reserved.',
    status='Approved',
    marketing_remarks='Excellent proposal with strong industrial alignment and mitigations. Approved.',
    submitted_by=superuser,
    reviewed_by=marketing_user
)


# --- BILLING LIFECYCLE CASES ---
# Make sure we use a mock PDF path in media folder to make it look 100% authentic and robust
mock_pdf_path = 'bills/pdfs/mock_invoice.pdf'

# Case A: Bill submitted by a trainer (SUBMITTED)
bill_a = Bill.objects.create(
    trainer=trainer_user,
    bill_title='Honorarium for Advanced ML Course - Week 1',
    bill_number='INV/2026/001',
    bill_amount=45000.00,
    training_program='Advanced Machine Learning & Neural Networks',
    bill_pdf=mock_pdf_path,
    current_status='SUBMITTED',
    remarks=''
)
BillHistory.objects.create(bill=bill_a, action_taken='Bill Submitted', action_by=trainer_user, remarks='First week billing for ML course.')

# Case B: Bill under Accounts review (UNDER_ACCOUNTS_REVIEW)
bill_b = Bill.objects.create(
    trainer=trainer_user,
    bill_title='Travel & Logistics Reimbursement - COEP',
    bill_number='INV/2026/002',
    bill_amount=12450.00,
    training_program='Cybersecurity Incident Response Bootcamp',
    bill_pdf=mock_pdf_path,
    current_status='UNDER_ACCOUNTS_REVIEW',
    remarks=''
)
BillHistory.objects.create(bill=bill_b, action_taken='Bill Submitted', action_by=trainer_user, remarks='Flight ticket and local travel bills attached.')
BillHistory.objects.create(bill=bill_b, action_taken='Moved to Accounts Review', action_by=accounts_user, remarks='Reviewing receipt validity.')

# Case C: Bill approved by Accounts (APPROVED_BY_ACCOUNTS)
bill_c = Bill.objects.create(
    trainer=trainer_user,
    bill_title='Full-Stack Bootcamp Lab Coordination Fees',
    bill_number='INV/2026/003',
    bill_amount=35000.00,
    training_program='Full-Stack Software Engineering Accelerator',
    bill_pdf=mock_pdf_path,
    current_status='APPROVED_BY_ACCOUNTS',
    remarks=''
)
BillHistory.objects.create(bill=bill_c, action_taken='Bill Submitted', action_by=trainer_user, remarks='')
BillHistory.objects.create(bill=bill_c, action_taken='Approved by Accounts Department', action_by=accounts_user, remarks='Receipts verified, billing parameters aligned.')

# Case D: Bill rejected by Accounts (REJECTED_BY_ACCOUNTS)
bill_d = Bill.objects.create(
    trainer=trainer_user,
    bill_title='Miscellaneous Consumables reimbursement',
    bill_number='INV/2026/004',
    bill_amount=8200.00,
    training_program='Cloud Architecture & DevOps Masterclass',
    bill_pdf=mock_pdf_path,
    current_status='REJECTED_BY_ACCOUNTS',
    remarks='No valid invoices/receipts uploaded. Please re-upload with clear JPEG/PDF receipts for the electronics purchased.'
)
BillHistory.objects.create(bill=bill_d, action_taken='Bill Submitted', action_by=trainer_user, remarks='')
BillHistory.objects.create(bill=bill_d, action_taken='Rejected by Accounts Department', action_by=accounts_user, remarks='No valid invoices/receipts uploaded. Please re-upload with clear JPEG/PDF receipts for the electronics purchased.')

# Case E: Bill under Trainer Admin review (UNDER_TRAINER_ADMIN_REVIEW)
bill_e = Bill.objects.create(
    trainer=trainer_user,
    bill_title='Masterclass Lecture Delivery - VJTI',
    bill_number='INV/2026/005',
    bill_amount=60000.00,
    training_program='Cloud Architecture & DevOps Masterclass',
    bill_pdf=mock_pdf_path,
    current_status='UNDER_TRAINER_ADMIN_REVIEW',
    remarks=''
)
BillHistory.objects.create(bill=bill_e, action_taken='Bill Submitted', action_by=trainer_user, remarks='')
BillHistory.objects.create(bill=bill_e, action_taken='Approved by Accounts Department', action_by=accounts_user, remarks='')
BillHistory.objects.create(bill=bill_e, action_taken='Moved to Trainer Admin Review', action_by=trainer_admin_user, remarks='')

# Case F: Bill payment cleared (PAYMENT_CLEARED)
bill_f = Bill.objects.create(
    trainer=trainer_user,
    bill_title='AI National Capability - Capstone Coordination',
    bill_number='INV/2026/006',
    bill_amount=120000.00,
    training_program='Artificial Intelligence & Big Data Analytics',
    bill_pdf=mock_pdf_path,
    current_status='PAYMENT_CLEARED',
    final_approved_at=timezone.now() - timedelta(days=1),
    remarks=''
)
BillHistory.objects.create(bill=bill_f, action_taken='Bill Submitted', action_by=trainer_user, remarks='')
BillHistory.objects.create(bill=bill_f, action_taken='Approved by Accounts Department', action_by=accounts_user, remarks='')
BillHistory.objects.create(bill=bill_f, action_taken='Payment Cleared by Trainer Admin', action_by=trainer_admin_user, remarks='Completed. Bank transaction TXN-AI-88321.')

# Case G: Bill rejected by Trainer Admin (REJECTED_BY_TRAINER_ADMIN)
bill_g = Bill.objects.create(
    trainer=trainer_user,
    bill_title='EVM Smart Contract Audit Consultations',
    bill_number='INV/2026/007',
    bill_amount=95000.00,
    training_program='Blockchain & Smart Contracts Specialization',
    bill_pdf=mock_pdf_path,
    current_status='REJECTED_BY_TRAINER_ADMIN',
    remarks='Deviation in pre-approved hourly consulting rates. Please coordinate with Trainer Admin to adjust consulting fees.'
)
BillHistory.objects.create(bill=bill_g, action_taken='Bill Submitted', action_by=trainer_user, remarks='')
BillHistory.objects.create(bill=bill_g, action_taken='Approved by Accounts Department', action_by=accounts_user, remarks='')
BillHistory.objects.create(bill=bill_g, action_taken='Rejected by Trainer Admin', action_by=trainer_admin_user, remarks='Deviation in pre-approved hourly consulting rates. Please coordinate with Trainer Admin to adjust consulting fees.')


print("All real-like dummy data and workflow cases created successfully!")
