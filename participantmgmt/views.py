import json
import os
import re
from uuid import uuid4
from datetime import date
from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

try:
	import requests
except Exception:
	requests = None

from participantmgmt.forms import (
	AcademicDetailsForm,
	CourseSelectionForm,
	LoginForm,
	PAYMENT_METHOD_CHOICES,
	PaymentForm,
	PersonalDetailsForm,
	ParticipantProfileForm,
)
from participantmgmt.models import Participant, ParticipantGuardian, Course, Program
import logging
from django.db import DatabaseError, connections

logger = logging.getLogger(__name__)


ADMISSION_SESSION_KEY = 'admission_draft'
PARTICIPANT_SESSION_KEY = 'participant_id'
DOCUMENT_TYPE_CHOICES = [
	('aadhaar_card', 'Aadhaar Card'),
	('pan_card', 'PAN Card'),
	('tenth_marksheet', '10th Marksheet'),
	('twelfth_marksheet', '12th Marksheet'),
	('graduation_certificate', 'Graduation Certificate'),
	('transfer_certificate', 'Transfer Certificate'),
	('passport_photo', 'Passport Size Photo'),
	('other_document', 'Other Document'),
]

DOCUMENT_TYPE_LABELS = dict(DOCUMENT_TYPE_CHOICES)

def _ensure_session_key(request):
	if not request.session.session_key:
		request.session.create()
	return request.session.session_key


def _get_admission_draft(request):
	return request.session.get(ADMISSION_SESSION_KEY, {
		'personal': {},
		'academic': {},
		'course': {},
		'payment': {},
		'documents': [],
	})


def _save_admission_draft(request, draft):
	request.session[ADMISSION_SESSION_KEY] = draft
	request.session.modified = True


def _clear_admission_draft(request):
	request.session.pop(ADMISSION_SESSION_KEY, None)
	request.session.modified = True


def _get_logged_in_participant(request):
	participant_id = request.session.get(PARTICIPANT_SESSION_KEY)
	if not participant_id:
		return None
	return Participant.objects.using('server').filter(participant_id=participant_id).first()


def _login_participant(request, participant):
	request.session[PARTICIPANT_SESSION_KEY] = participant.participant_id
	request.session['participant_username'] = participant.username or ''
	request.session.modified = True


def _logout_participant(request):
	request.session.pop(PARTICIPANT_SESSION_KEY, None)
	request.session.pop('participant_username', None)
	request.session.modified = True


def participant_login_required(view_func):
	@wraps(view_func)
	def wrapped_view(request, *args, **kwargs):
		participant = _get_logged_in_participant(request)
		if not participant:
			return redirect('participantmgmt:login')
		status = (participant.status or '').strip().lower()
		if status != 'approved':
			_logout_participant(request)
			if status == 'rejected':
				messages.error(request, 'Rejected by admin.')
			else:
				messages.warning(request, 'Waiting for approval.')
			return redirect('participantmgmt:login')
		request.participant = participant
		return view_func(request, *args, **kwargs)
	return wrapped_view


def _admission_doc_rows(draft):
	documents = draft.get('documents') or []
	if not documents:
		return [{'index': 1, 'document_type': '', 'file_name': ''}]
	rows = []
	for index, document in enumerate(documents, start=1):
		rows.append({
			'index': index,
			'document_type': document.get('document_type', ''),
			'file_name': document.get('original_name', ''),
		})
	return rows


def _post_document_to_api(api_url, api_key, title, file_type, related_module, related_id, uploaded_file, file_name):
	if requests is None:
		raise ValueError('Requests library is not available.')
	try:
		uploaded_file.seek(0)
	except Exception:
		pass
	content_type = getattr(uploaded_file, 'content_type', None) or 'application/octet-stream'
	if file_name.lower().endswith('.pdf'):
		content_type = 'application/pdf'
	elif file_name.lower().endswith(('.jpg', '.jpeg')):
		content_type = 'image/jpeg'
	elif file_name.lower().endswith('.png'):
		content_type = 'image/png'
	elif file_name.lower().endswith('.doc'):
		content_type = 'application/msword'
	elif file_name.lower().endswith('.docx'):
		content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

	headers = {}
	if api_key:
		headers['Authorization'] = f'Bearer {api_key}'

	response = requests.post(
		api_url,
		data={
			'title': title,
			'file_type': file_type,
			'related_module': related_module,
			'related_id': related_id,
		},
		files={
			'file': (file_name, uploaded_file, content_type),
		},
		headers=headers,
		timeout=15,
	)
	if response.status_code not in (200, 201):
		raise ValueError(f'Document upload failed: {response.status_code} {response.text}')
	try:
		payload = response.json()
	except Exception:
		payload = {'status_code': response.status_code, 'response_text': response.text}
	if not isinstance(payload, dict):
		payload = {'status_code': response.status_code, 'response_text': response.text}
	return payload


@csrf_exempt
def document_upload_api(request):
	if request.method != 'POST':
		return JsonResponse({'detail': 'Method not allowed.'}, status=405)

	title = (request.POST.get('title') or '').strip()
	file_type = (request.POST.get('file_type') or '').strip()
	related_module = (request.POST.get('related_module') or '').strip()
	related_id = (request.POST.get('related_id') or '').strip()
	uploaded_file = request.FILES.get('file')

	if not title or not file_type or not related_module or not related_id or not uploaded_file:
		return JsonResponse({'detail': 'title, file_type, related_module, related_id, and file are required.'}, status=400)

	api_url = (os.environ.get('DOCUMENT_UPLOAD_API_URL') or getattr(settings, 'DOCUMENT_UPLOAD_API_URL', '')).strip()
	api_key = os.environ.get('DOCUMENT_UPLOAD_API_KEY') or getattr(settings, 'DOCUMENT_UPLOAD_API_KEY', None)
	if not api_url:
		return JsonResponse({'detail': 'Document upload API is not configured.'}, status=503)

	filename = get_valid_filename(uploaded_file.name)
	payload = _post_document_to_api(
		api_url,
		api_key,
		title,
		file_type,
		related_module,
		related_id,
		uploaded_file,
		filename,
	)
	return JsonResponse(payload, status=201)


def _upload_document_via_api(username, document):
	api_url = (os.environ.get('DOCUMENT_UPLOAD_API_URL') or getattr(settings, 'DOCUMENT_UPLOAD_API_URL', '')).strip()
	api_key = os.environ.get('DOCUMENT_UPLOAD_API_KEY') or getattr(settings, 'DOCUMENT_UPLOAD_API_KEY', None)
	if not api_url:
		raise ValueError('Document upload API is not configured.')
	# Support either an in-memory uploaded file (document['temp_file'])
	# or a path saved in storage (document['temp_path']). This lets callers
	# upload immediately (without writing to admission_drafts) by passing
	# the uploaded file object.
	temp_file_obj = document.get('temp_file')
	temp_path = document.get('temp_path', '')
	if not temp_file_obj and not temp_path:
		raise ValueError('Document file is missing.')

	title = DOCUMENT_TYPE_LABELS.get(document.get('document_type', ''), document.get('document_type', '').replace('_', ' ').title())
	file_name = get_valid_filename(document.get('original_name') or (os.path.basename(temp_path) if temp_path else 'document'))
	if temp_file_obj:
		file_ctx = None
		upload_source = temp_file_obj
	else:
		file_ctx = default_storage.open(temp_path, 'rb')
		upload_source = file_ctx

	try:
		response = _post_document_to_api(
			api_url,
			api_key,
			title,
			document.get('document_type', ''),
			'participant_module',
			username,
			upload_source,
			file_name,
		)
	finally:
		if file_ctx:
			try:
				file_ctx.close()
			except Exception:
				pass
	return response


def _extract_document_rows(post_data, files_data):
	indices = set()
	pattern = re.compile(r'^(document_type|document_file)_(\d+)$')
	for key in list(post_data.keys()) + list(files_data.keys()):
		match = pattern.match(key)
		if match:
			indices.add(int(match.group(2)))

	documents = []
	incomplete = []
	for index in sorted(indices):
		document_type = post_data.get(f'document_type_{index}', '').strip()
		uploaded_file = files_data.get(f'document_file_{index}')
		if document_type and uploaded_file:
			documents.append({
				'document_type': document_type,
				'original_name': uploaded_file.name,
				'temp_file': uploaded_file,
			})
		elif document_type or uploaded_file:
			incomplete.append(index)
	return documents, incomplete


def _posted_document_rows(post_data, files_data):
	indices = set()
	pattern = re.compile(r'^(document_type|document_file)_(\d+)$')
	for key in list(post_data.keys()) + list(files_data.keys()):
		match = pattern.match(key)
		if match:
			indices.add(int(match.group(2)))

	rows = []
	for index in sorted(indices):
		file_object = files_data.get(f'document_file_{index}')
		rows.append({
			'index': index,
			'document_type': post_data.get(f'document_type_{index}', ''),
			'file_name': getattr(file_object, 'name', ''),
		})
	return rows or [{'index': 1, 'document_type': '', 'file_name': ''}]


def _course_catalog_from_db():
	catalog = {}
	try:
		qs = Program.objects.using('server').all().order_by('program_name')
		for program in qs:
			catalog[program.course_code] = {
				'program_id': program.course_id,
				'program_code': program.course_code,
				'program_name': program.course_name,
				'program_image': program.course_image or '',
				'description': program.description or '',
				'duration_days': program.duration_hours,
				'duration_display': f'{program.duration_hours} Days',
				'category_id': program.category_id,
				'category_label': program.level,
				'start_date': program.start_date.isoformat() if program.start_date else '',
				'end_date': program.end_date.isoformat() if program.end_date else '',
				'enrollment_open': program.enrollment_open,
				'status': program.status,
				'fees': '',
				'fees_display': 'To be decided',
				# Compatibility keys used by existing templates/scripts.
				'course_id': program.course_id,
				'course_code': program.course_code,
				'course_name': program.course_name,
				'course_image': program.course_image or '',
				'duration_hours': program.duration_hours,
				'level': program.level,
			}
	except DatabaseError as e:
		logger.warning('Could not load program catalog from DB: %s', e)
		# Return empty catalog so UI can still function while DB is down.
		return {}
	return catalog


def _course_snapshot(course_code):
	return _course_catalog_from_db().get(course_code, {})


def _attendance_data_for_participant(participant):
	stats = {
		'total': 0,
		'present': 0,
		'absent': 0,
		'other': 0,
		'percentage': 0,
	}
	if not participant or participant.user_id is None:
		return [], stats

	try:
		with connections['server'].cursor() as cursor:
			cursor.execute(
				'SELECT enrollment_id, status FROM attendance WHERE enrollment_id = %s',
				[participant.user_id],
			)
			rows = cursor.fetchall()
	except DatabaseError as error:
		logger.warning('Could not load attendance for participant %s: %s', participant.user_id, error)
		return [], stats

	records = []
	for enrollment_id, status in rows:
		status_text = (status or '').strip() or 'Unknown'
		status_key = status_text.lower()
		if status_key == 'present':
			stats['present'] += 1
		elif status_key == 'absent':
			stats['absent'] += 1
		else:
			stats['other'] += 1
		records.append({
			'enrollment_id': enrollment_id,
			'status': status_text,
		})

	stats['total'] = len(records)
	if stats['total']:
		stats['percentage'] = round((stats['present'] / stats['total']) * 100)
	return records, stats


def _generate_local_admission_no():
	base = f"ENR{timezone.now().strftime('%Y%m%d%H%M%S')}"
	for _ in range(20):
		candidate = f"{base}{uuid4().hex[:6].upper()}"
		if not Participant.objects.using('server').filter(admission_no=candidate).exists():
			return candidate
	raise ValueError('Unable to generate a unique admission number.')


def _personal_initial_data(personal_data):
	initial = dict(personal_data or {})
	if initial.get('dob') and isinstance(initial['dob'], str):
		try:
			initial['dob'] = date.fromisoformat(initial['dob'])
		except ValueError:
			initial['dob'] = None
	return initial


def _guardian_initial_data(personal_data):
	initial = dict(personal_data or {})
	return {
		'guardian_name': initial.get('guardian_name', ''),
		'relationship': initial.get('relationship', ''),
		'guardian_mobile': initial.get('guardian_mobile', ''),
		'guardian_email': initial.get('guardian_email', ''),
		'guardian_address': initial.get('guardian_address', ''),
	}


def _manifest_for_draft(request, draft):
	return {
		'student_name': f"{draft.get('personal', {}).get('first_name', '')} {draft.get('personal', {}).get('last_name', '')}".strip(),
		'username': draft.get('course', {}).get('username', ''),
		'email': draft.get('personal', {}).get('email', ''),
		'course': draft.get('course', {}).get('course', ''),
		'course_code': draft.get('course', {}).get('course_code', ''),
		'academic_year': draft.get('academic', {}).get('academic_year', ''),
		'payment': draft.get('payment', {}),
		'documents': draft.get('documents', []),
		'submitted_at': timezone.now().isoformat(),
		'course_snapshot': _course_snapshot(draft.get('course', {}).get('course_code', '')),
		'session_key': request.session.session_key,
	}


def _finalize_admission(request, draft, receipt_file=None):
	personal = draft.get('personal', {})
	academic = draft.get('academic', {})
	course = draft.get('course', {})
	payment = draft.get('payment', {})
	documents = draft.get('documents', [])

	username = (course.get('username') or '').strip()
	password1 = course.get('password1') or ''
	if not username:
		raise ValueError('Username is required.')
	if not password1:
		raise ValueError('Password is required.')
	if Participant.objects.using('server').filter(username=username).exists():
		raise ValueError('That username is already taken.')

	selected_program_code = course.get('program_code') or course.get('course_code', '')
	if not selected_program_code:
		raise ValueError('Please select a program.')
	program_obj = Program.objects.using('server').filter(program_code=selected_program_code).first()
	if not program_obj:
		raise ValueError('Selected program is not available.')

	admission_no = _generate_local_admission_no()

	participant = Participant.objects.using('server').create(
		admission_no=admission_no,
		username=username,
		password_hash='',
		first_name=personal.get('first_name', ''),
		last_name=personal.get('last_name', ''),
		dob=date.fromisoformat(personal['dob']) if personal.get('dob') else None,
		gender=personal.get('gender', ''),
		mobile=personal.get('mobile', ''),
		email=personal.get('email', ''),
		course=None,
		academic_year_id=academic.get('academic_year', ''),
		status='pending',
	)
	if participant.user_id is None:
		participant.user_id = participant.participant_id
		participant.save(using='server', update_fields=['user_id'])
	participant.set_password(password1)
	participant.save(using='server', update_fields=['password_hash'])

	guardian_name = personal.get('guardian_name', '').strip()
	guardian = None
	if guardian_name:
		guardian = ParticipantGuardian.objects.using('server').create(
			participant=participant,
			guardian_name=guardian_name,
			relationship=personal.get('relationship', ''),
			mobile=personal.get('guardian_mobile', ''),
			email=personal.get('guardian_email', ''),
			address=personal.get('guardian_address', ''),
		)

	final_documents = []
	try:
		for document in documents:
			if document.get('upload_response'):
				uploaded_document = document.get('upload_response')
			else:
				uploaded_document = _upload_document_via_api(participant.username, document)
			final_documents.append({
				'document_type': document['document_type'],
				'title': DOCUMENT_TYPE_LABELS.get(document.get('document_type', ''), document.get('document_type', '')),
				'upload_response': uploaded_document,
			})
	except Exception:
		if guardian is not None:
			guardian.delete(using='server')
		participant.delete(using='server')
		raise

	if receipt_file is not None:
		stored_receipt_name = get_valid_filename(getattr(receipt_file, 'name', 'receipt'))
		api_response = _upload_document_via_api(participant.username, {
			'document_type': 'payment_receipt',
			'original_name': stored_receipt_name,
			'temp_file': receipt_file,
		})
		payment['receipt_upload_response'] = api_response

	# Keep the document upload results inside the draft/session data only.
	draft['documents'] = final_documents
	draft['payment'] = payment

	# Try to obtain/generate an admission_no override from external API if configured.
	def _generate_enrollment_id(participant):
		# If API URL provided in settings, call it
		api_url = getattr(settings, 'ENROLLMENT_API_URL', None)
		api_key = getattr(settings, 'ENROLLMENT_API_KEY', None)
		payload = {
			'username': participant.username,
			'first_name': participant.first_name,
			'last_name': participant.last_name,
			'email': participant.email,
			'course': getattr(participant.course, 'course_name', None),
			'academic_year': participant.academic_year,
		}
		if api_url and requests:
			try:
				headers = {'Content-Type': 'application/json'}
				if api_key:
					headers['Authorization'] = f'Bearer {api_key}'
				resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
				if resp.status_code in (200, 201):
					data = resp.json()
					# Expecting the API to return an `enrollment_id` field
					if isinstance(data, dict) and data.get('enrollment_id'):
						return str(data.get('enrollment_id'))
			except Exception:
				pass

		# Fallback: generate a local enrollment id
		return f"ENR{timezone.now().strftime('%Y%m%d')}{uuid4().hex[:8].upper()}"

	api_admission_no = _generate_enrollment_id(participant)
	if api_admission_no and api_admission_no != participant.admission_no:
		if not Participant.objects.using('server').filter(admission_no=api_admission_no).exists():
			participant.admission_no = api_admission_no
			participant.save(using='server', update_fields=['admission_no'])

	return participant


def landing(request):
	return render(request, 'landing.html')


def register_view(request):
	if _get_logged_in_participant(request):
		return redirect('participantmgmt:home')
	draft = _get_admission_draft(request)
	initial_data = _personal_initial_data(draft.get('personal', {}))
	initial_data.update(_guardian_initial_data(draft.get('personal', {})))
	if request.method == 'POST':
		form = PersonalDetailsForm(request.POST, request.FILES)
		if form.is_valid():
			draft['personal'] = {
				'first_name': form.cleaned_data['first_name'],
				'last_name': form.cleaned_data['last_name'],
				'dob': form.cleaned_data['dob'].isoformat(),
				'gender': form.cleaned_data['gender'],
				'mobile': form.cleaned_data['mobile'],
				'email': form.cleaned_data['email'],
				'address': form.cleaned_data['address'],
				'guardian_name': form.cleaned_data['guardian_name'],
				'relationship': form.cleaned_data['relationship'],
				'guardian_mobile': form.cleaned_data['guardian_mobile'],
				'guardian_email': form.cleaned_data['guardian_email'],
				'guardian_address': form.cleaned_data['guardian_address'],
			}
			if form.cleaned_data.get('photo'):
				photo_response = _upload_document_via_api(_ensure_session_key(request), {
					'document_type': 'passport_photo',
					'original_name': getattr(form.cleaned_data['photo'], 'name', 'passport_photo'),
					'temp_file': form.cleaned_data['photo'],
				})
				draft['personal']['photo_upload_response'] = photo_response
			_save_admission_draft(request, draft)
			return redirect('participantmgmt:register_documents')
	else:
		form = PersonalDetailsForm(initial=initial_data)
	return render(request, 'accounts/register_step1.html', {
		'form': form,
	})


def register_documents_view(request):
	if _get_logged_in_participant(request):
		return redirect('participantmgmt:home')
	draft = _get_admission_draft(request)
	if not draft.get('personal'):
		return redirect('participantmgmt:register')

	academic_form = AcademicDetailsForm(initial=draft.get('academic', {}))
	document_rows = _admission_doc_rows(draft)
	if request.method == 'POST':
		academic_form = AcademicDetailsForm(request.POST)
		documents, incomplete_rows = _extract_document_rows(request.POST, request.FILES)
		if academic_form.is_valid() and not incomplete_rows:
			# Do not persist files to local admission_drafts; upload each document
			# immediately to the configured document API and store only the API
			# responses in the draft's documents list.
			draft['academic'] = academic_form.cleaned_data
			draft_documents = []
			session_key = _ensure_session_key(request)
			for document in documents:
				# Attempt to upload directly using the in-memory uploaded file
				try:
					document_payload = {
						'document_type': document['document_type'],
						'original_name': document['original_name'],
						'temp_file': document.get('temp_file'),
					}
					upload_response = _upload_document_via_api(session_key, document_payload)
				except Exception as e:
					# If upload fails, add an error and stop processing
					academic_form.add_error(None, f"Uploading document '{document.get('original_name')}' failed: {e}")
					document_rows = _posted_document_rows(request.POST, request.FILES)
					return render(request, 'accounts/register_step2.html', {
						'form': academic_form,
						'document_rows': document_rows,
						'document_choices': DOCUMENT_TYPE_CHOICES,
					})

				draft_documents.append({
					'document_type': document['document_type'],
					'original_name': document['original_name'],
					'upload_response': upload_response,
				})

			draft['documents'] = draft_documents
			_save_admission_draft(request, draft)
			return redirect('participantmgmt:register_course')
		if incomplete_rows:
			academic_form.add_error(None, 'Each document row must include both a document type and a file.')
		document_rows = _posted_document_rows(request.POST, request.FILES)
	return render(request, 'accounts/register_step2.html', {
		'form': academic_form,
		'document_rows': document_rows,
		'document_choices': DOCUMENT_TYPE_CHOICES,
	})


def register_course_view(request):
	if _get_logged_in_participant(request):
		return redirect('participantmgmt:home')
	draft = _get_admission_draft(request)
	if not draft.get('personal') or not draft.get('academic'):
		return redirect('participantmgmt:register')

	course_catalog = _course_catalog_from_db()
	course_choices = [(code, item['course_name']) for code, item in course_catalog.items()]
	initial_course = dict(draft.get('course', {}))
	if initial_course.get('course_code'):
		initial_course['course'] = initial_course['course_code']
	form = CourseSelectionForm(initial=initial_course, course_choices=course_choices)
	if request.method == 'POST':
		form = CourseSelectionForm(request.POST, course_choices=course_choices)
		if form.is_valid():
			selected_course_code = form.cleaned_data['course']
			selected_course = course_catalog.get(selected_course_code)
			if not selected_course:
				form.add_error('course', 'Selected course is not available.')
			elif Participant.objects.using('server').filter(username=form.cleaned_data['username']).exists():
				form.add_error('username', 'This username is already taken.')
			else:
				draft['course'] = {
					'program': selected_course['program_name'],
					'program_code': selected_course['program_code'],
					'program_image': selected_course['program_image'],
					'description': selected_course['description'],
					'duration_days': selected_course['duration_days'],
					'duration_display': selected_course['duration_display'],
					'fees': selected_course['fees'],
					'fees_display': selected_course['fees_display'],
					'category_id': selected_course['category_id'],
					'category_label': selected_course['category_label'],
					'start_date': selected_course['start_date'],
					'end_date': selected_course['end_date'],
					'enrollment_open': selected_course['enrollment_open'],
					'status': selected_course['status'],
					# Compatibility keys used by current templates/scripts.
					'course': selected_course['program_name'],
					'course_code': selected_course['program_code'],
					'course_image': selected_course['program_image'],
					'duration_hours': selected_course['duration_days'],
					'level': selected_course['category_label'],
					'username': form.cleaned_data['username'],
					'password1': form.cleaned_data['password1'],
					'password2': form.cleaned_data['password2'],
				}
				draft['program'] = dict(draft['course'])
				_save_admission_draft(request, draft)
				return redirect('participantmgmt:register_payment')
	return render(request, 'accounts/register_step3.html', {
		'form': form,
		'course_catalog': course_catalog,
		'program_catalog': course_catalog,
	})


def register_payment_view(request):
	if _get_logged_in_participant(request):
		return redirect('participantmgmt:home')
	draft = _get_admission_draft(request)
	if not draft.get('personal') or not draft.get('academic') or not draft.get('course'):
		return redirect('participantmgmt:register')

	form = PaymentForm(initial=draft.get('payment', {}))
	if request.method == 'POST':
		form = PaymentForm(request.POST, request.FILES)
		if form.is_valid():
			draft['payment'] = {
				'payment_method': form.cleaned_data['payment_method'],
				'transaction_id': form.cleaned_data['transaction_id'],
			}
			receipt_file = form.cleaned_data.get('receipt')
			if receipt_file:
				draft['payment']['receipt_name'] = getattr(receipt_file, 'name', '')

			try:
				participant = _finalize_admission(request, draft, receipt_file=receipt_file)
			except ValueError as error:
				form.add_error('payment_method', str(error))
			else:
				_clear_admission_draft(request)
				messages.success(request, f'Application submitted successfully for {participant.get_full_name()}. Please wait for admin approval.')
				return redirect('participantmgmt:login')

	return render(request, 'accounts/register_payment.html', {
		'form': form,
		'draft': draft,
		'course_summary': _course_snapshot(draft.get('course', {}).get('course_code', '')),
		'program_summary': _course_snapshot(draft.get('program', {}).get('course_code', draft.get('course', {}).get('course_code', ''))),
		'payment_methods': PAYMENT_METHOD_CHOICES,
	})


def login_view(request):
	if _get_logged_in_participant(request):
		return redirect('participantmgmt:home')
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			participant = Participant.objects.using('server').filter(username=username).first()
			if participant:
				status = (participant.status or '').strip().lower()
				if status == 'pending':
					messages.warning(request, 'Waiting for approval.')
				elif status == 'rejected':
					messages.error(request, 'Rejected by admin.')
				elif status != 'approved':
					messages.error(request, 'Your account is not approved yet.')
				elif participant.check_password(password):
					_login_participant(request, participant)
					return redirect('participantmgmt:home')
				else:
					messages.error(request, 'Invalid username or password.')
			else:
				messages.error(request, 'Invalid username or password.')
	else:
		form = LoginForm()
	return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
	_logout_participant(request)
	messages.success(request, 'You have been logged out successfully.')
	return redirect('participantmgmt:landing')


@participant_login_required
def home(request):
	participant = getattr(request, 'participant', None)
	if not participant:
		return redirect('participantmgmt:landing')
	attendance_records, attendance_stats = _attendance_data_for_participant(participant)
	return render(request, 'dashboard/home.html', {
		'student': participant,
		'attendance_pct': attendance_stats['percentage'],
		'recent_attendance': attendance_records[:5],
		'recent_assessments': [],
		'recent_results': [],
		'notifications': [],
		'total_subjects': 0,
		'total_attendance_days': attendance_stats['total'],
		'assessment_avg': 0,
		'result_overall_pct': 0,
		'pending_assessments': 0,
	})


@participant_login_required
def profile_view(request):
	participant = getattr(request, 'participant', None)
	attendance_records, attendance_stats = _attendance_data_for_participant(participant)
	return render(request, 'students/profile.html', {
		'student': participant,
		'attendance_pct': attendance_stats['percentage'],
		'attendance_records': attendance_records,
	})


@participant_login_required
def profile_edit(request):
	participant = getattr(request, 'participant', None)
	if request.method == 'POST':
		form = ParticipantProfileForm(request.POST, request.FILES, instance=participant)
		if form.is_valid():
			form.save()
			messages.success(request, 'Profile updated successfully!')
			return redirect('participantmgmt:profile')
		messages.error(request, 'Please correct the errors.')
	else:
		form = ParticipantProfileForm(instance=participant)
	return render(request, 'students/profile_edit.html', {'form': form, 'student': participant})


@participant_login_required
def attendance_view(request):
	participant = getattr(request, 'participant', None)
	attendance_records, attendance_stats = _attendance_data_for_participant(participant)
	return render(request, 'students/attendance.html', {
		'student': participant,
		'attendance_records': attendance_records,
		'percentage': attendance_stats['percentage'],
		'present_count': attendance_stats['present'],
		'absent_count': attendance_stats['absent'],
		'other_count': attendance_stats['other'],
		'total_count': attendance_stats['total'],
	})


@participant_login_required
def assessment_view(request):
	participant = getattr(request, 'participant', None)
	return render(request, 'students/assessment.html', {
		'student': participant,
		'assessments': [],
		'completed_count': 0,
		'pending_count': 0,
		'average_score': 0,
	})


@participant_login_required
def results_view(request):
	participant = getattr(request, 'participant', None)
	return render(request, 'students/results.html', {
		'student': participant,
		'results': [],
		'semesters': [],
		'semester_filter': '',
		'overall_pct': 0,
	})