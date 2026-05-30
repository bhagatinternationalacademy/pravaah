from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import EmailNotificationLog
from .services import (
    send_account_verification_email,
    send_student_registration_confirmation_email,
    send_verification_confirmation_email,
    send_password_reset_otp_email
)

def email_dashboard(request):
    """Fetches all sent notification logs sorted descending by creation date."""
    emails = EmailNotificationLog.objects.all().order_by('-created_at')
    return render(
        request,
        'dashboard/email_dashboard.html',
        {'emails': emails}
    )

def send_test_email(request):
    """Facilitates sending dynamic simulated testing notifications from Dashboard GUI."""
    if request.method == 'POST':
        email = request.POST.get('email')
        event_type = request.POST.get('event_type')
        first_name = request.POST.get('first_name', 'Test User')
        username = request.POST.get('username', 'testuser')

        if not email:
            messages.error(request, 'Please provide a recipient email address.')
            return redirect('email_dashboard')

        user = User(username=username, email=email, first_name=first_name)
        host = request.get_host()

        try:
            if event_type == 'ACCOUNT_VERIFICATION':
                send_account_verification_email(user, host)
                messages.success(request, f'Account verification email sent to {email} successfully!')
            elif event_type == 'VERIFY_CONFIRMATION':
                send_verification_confirmation_email(user)
                messages.success(request, f'Verification confirmation email sent to {email} successfully!')
            elif event_type == 'PASSWORD_RESET_OTP':
                reset_page = f"http://{host}/reset-password/"
                send_password_reset_otp_email(user, reset_page)
                messages.success(request, f'Password reset OTP email sent to {email} successfully!')
            elif event_type == 'REGISTRATION_SUCCESS':
                send_student_registration_confirmation_email(user, host)
                messages.success(request, f'registration Confirmation email sent to {email} successfully!')
            else:
                messages.error(request, 'Unsupported email event type selected.')
        except Exception as error:
            messages.error(request, f'Failed to process SMTP relay: {str(error)}')

    return redirect('email_dashboard')


# ==========================================
# 8. DRF Document Management REST API Endpoints
# ==========================================
from django.http import FileResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Document
from .serializers import DocumentSerializer

@api_view(['POST'])
def upload_document_api(request):
    """DRF endpoint to upload a generic document."""
    serializer = DocumentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_documents_api(request):
    """DRF endpoint to fetch list of all uploaded documents."""
    documents = Document.objects.all()
    serializer = DocumentSerializer(documents, many=True)
    return Response({
        'message': 'Documents fetched successfully',
        'data': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def documents_by_module_api(request, module_name):
    """DRF endpoint to fetch all documents related to a specific module."""
    documents = Document.objects.filter(related_module=module_name)
    serializer = DocumentSerializer(documents, many=True)
    return Response({
        'message': f'{module_name} documents fetched successfully',
        'data': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_document_api(request, document_id):
    """DRF endpoint to retrieve a single document details."""
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return Response({'message': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = DocumentSerializer(document)
    return Response({
        'message': 'Document fetched successfully',
        'data': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_document_api(request, document_id):
    """DRF endpoint to delete a document resource."""
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return Response({'message': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    document.delete()
    return Response({'message': 'Document deleted successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def download_document_api(request, document_id):
    """DRF endpoint to stream download raw document files."""
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return Response({'message': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    return FileResponse(document.file.open(), as_attachment=True)


# ==========================================
# 9. DRF Calendar Event REST API Endpoints
# ==========================================
from .serializers import CalendarEventSerializer
from .services import create_event as service_create_event, update_event as service_update_event

@api_view(['GET', 'POST'])
def list_create_events_api(request):
    """DRF endpoint to list user events or create a new event (with conflict checking)."""
    if request.method == 'GET':
        user_id = request.query_params.get('user_id') or (request.user.id if request.user.is_authenticated else None)
        if not user_id:
            return Response({'message': 'User parameter or authenticated user session required.'}, status=status.HTTP_400_BAD_REQUEST)
        events = CalendarEvent.objects.filter(user_id=user_id).order_by('start_time')
        serializer = CalendarEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == 'POST':
        user_id = request.data.get('user') or (request.user.id if request.user.is_authenticated else None)
        if not user_id:
            return Response({'message': 'User is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            event = service_create_event(
                user=user,
                title=request.data.get('title'),
                start_time=request.data.get('start_time'),
                end_time=request.data.get('end_time'),
                description=request.data.get('description'),
                location=request.data.get('location'),
                meeting_link=request.data.get('meeting_link')
            )
            serializer = CalendarEventSerializer(event)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def update_event_api(request, event_id):
    """DRF endpoint to update an existing calendar event (with conflict checking)."""
    try:
        kwargs = {}
        for field in ['title', 'start_time', 'end_time', 'description', 'location', 'meeting_link']:
            if field in request.data:
                kwargs[field] = request.data.get(field)
                
        event = service_update_event(event_id=event_id, **kwargs)
        serializer = CalendarEventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except CalendarEvent.DoesNotExist:
        return Response({'message': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_event_api(request, event_id):
    """DRF endpoint to delete a calendar event."""
    try:
        event = CalendarEvent.objects.get(id=event_id)
        event.delete()
        return Response({'message': 'Event deleted successfully.'}, status=status.HTTP_200_OK)
    except CalendarEvent.DoesNotExist:
        return Response({'message': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)


# ==========================================
# 10. Legacy HTML Calendar Views (Non-API)
# ==========================================
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, time, timedelta
from django.utils import timezone
from .models import CalendarEvent

@login_required
def calendar_legacy_view(request):
    """Legacy calendar view rendering standard HTML templates and handling event creation."""
    if request.method == "POST":
        title = request.POST.get("title")
        date_str = request.POST.get("date")

        if title and date_str:
            try:
                # Parse date and build timezone-aware start and end times (e.g. 9 AM - 10 AM)
                naive_date = datetime.strptime(date_str, "%Y-%m-%d")
                start_time = timezone.make_aware(datetime.combine(naive_date.date(), time(9, 0)))
                end_time = start_time + timedelta(hours=1)

                service_create_event(
                    user=request.user,
                    title=title,
                    start_time=start_time,
                    end_time=end_time
                )
                messages.success(request, "Event added successfully!")
            except ValueError as e:
                messages.error(request, f"Conflict: {str(e)}")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

        return redirect("calendar_legacy_view")

    # Fetch and format events for standard calendar.html rendering
    events = CalendarEvent.objects.filter(user=request.user).order_by('start_time')
    formatted_events = []
    for e in events:
        local_start = timezone.localtime(e.start_time)
        formatted_events.append({
            "id": e.id,
            "title": e.title,
            "date": local_start.strftime("%Y-%m-%d"),
            "user_name": e.user.username,
            "time": local_start.strftime("%H:%M")
        })

    return render(request, "calendar/calendar.html", {"events": formatted_events})


@login_required
def update_event_legacy_view(request, id):
    """Legacy-compatible event update endpoint via AJAX POST, checking for conflicts."""
    if request.method == "POST":
        title = request.POST.get("title")
        date_str = request.POST.get("date")

        if title and date_str:
            try:
                naive_date = datetime.strptime(date_str, "%Y-%m-%d")
                start_time = timezone.make_aware(datetime.combine(naive_date.date(), time(9, 0)))
                end_time = start_time + timedelta(hours=1)

                # Ensure event belongs to requesting user
                event = get_object_or_404(CalendarEvent, id=id, user=request.user)

                service_update_event(
                    event_id=event.id,
                    title=title,
                    start_time=start_time,
                    end_time=end_time
                )
                return JsonResponse({"status": "success"})
            except ValueError as e:
                return JsonResponse({"status": "error", "message": f"Conflict: {str(e)}"})
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request method."})


@login_required
def delete_event_legacy_view(request, id):
    """Legacy-compatible event deletion endpoint via POST."""
    if request.method == "POST":
        event = get_object_or_404(CalendarEvent, id=id, user=request.user)
        event.delete()
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error", "message": "Invalid request method."})
