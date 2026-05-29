from django.urls import path
from .views import (
    email_dashboard,
    send_test_email,
    upload_document_api,
    list_documents_api,
    documents_by_module_api,
    get_document_api,
    delete_document_api,
    download_document_api,
    list_create_events_api,
    update_event_api,
    delete_event_api,
    calendar_legacy_view,
    update_event_legacy_view,
    delete_event_legacy_view
)

urlpatterns = [
    path('dashboard/', email_dashboard, name='email_dashboard'),
    path('dashboard/send-test/', send_test_email, name='send_test_email'),
    
    # Document Management REST API
    path('documents/upload/', upload_document_api, name='upload_document_api'),
    path('documents/', list_documents_api, name='list_documents_api'),
    path('documents/module/<str:module_name>/', documents_by_module_api, name='documents_by_module_api'),
    path('documents/<int:document_id>/', get_document_api, name='get_document_api'),
    path('documents/<int:document_id>/delete/', delete_document_api, name='delete_document_api'),
    path('documents/<int:document_id>/download/', download_document_api, name='download_document_api'),
    
    # Calendar Event REST API
    path('calendar/', list_create_events_api, name='list_create_events_api'),
    path('calendar/update/<int:event_id>/', update_event_api, name='update_event_api'),
    path('calendar/delete/<int:event_id>/', delete_event_api, name='delete_event_api'),
    
    # Legacy HTML Calendar View Routes
    path('calendar/view/', calendar_legacy_view, name='calendar_legacy_view'),
    path('calendar/view/update/<int:id>/', update_event_legacy_view, name='update_event_legacy_view'),
    path('calendar/view/delete/<int:id>/', delete_event_legacy_view, name='delete_event_legacy_view'),
]
