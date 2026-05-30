from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='pravaah_landing'),
    path('future-proposals/', views.future_proposals_list, name='pravaah_future_proposals'),
    path('add-proposal/', views.add_proposal, name='pravaah_add_proposal'),
    
    path('gate-zero/', views.gate_zero_form, name='pravaah_gate_zero'),
    path('gate-zero/<int:proposal_id>/', views.gate_zero_form, name='pravaah_gate_zero_proposal'),
    
    path('gate-approval/', views.gate_approval_form, name='pravaah_gate_approval'),
    path('gate-approval/<int:proposal_id>/', views.gate_approval_form, name='pravaah_gate_approval_proposal'),
    
    path('marketing-queue/', views.marketing_queue, name='pravaah_marketing_queue'),
    path('marketing-queue/approve/<int:approval_id>/', views.approve_gate_approval, name='pravaah_approve_gate_approval'),
    path('marketing-queue/reject/<int:approval_id>/', views.reject_gate_approval, name='pravaah_reject_gate_approval'),
]
