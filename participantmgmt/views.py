import json
import re
from uuid import uuid4
from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.utils.text import slugify
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
from participantmgmt.models import Participant, ParticipantGuardian, Course


ADMISSION_SESSION_KEY = 'admission_draft'
TEMP_ADMISSION_FOLDER = 'admission_drafts'
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

COURSE_CATALOG = {
	'B.Tech CSE': {
		'duration': '4 Years',
		'fees': 'Rs. 1,20,000 per year',
		'description': 'A hands-on software engineering track with programming, web development, databases, cloud, and placement-focused labs.',
		'highlights': ['Full stack labs', 'Coding practice', 'Placement support'],
	},
	'B.Tech ECE': {
		'duration': '4 Years',
		'fees': 'Rs. 1,10,000 per year',
		'description': 'Electronics and communication fundamentals with embedded systems, signals, and industry-relevant projects.',
		'highlights': ['Embedded systems', 'Circuit design', 'Project work'],
	},
	'B.Tech ME': {
		'duration': '4 Years',
		'fees': 'Rs. 1,05,000 per year',
		'description': 'Mechanical engineering covering design, manufacturing, thermal systems, and practical workshops.',
		'highlights': ['CAD/CAM', 'Workshop practice', 'Industry projects'],
	},
	'B.Tech Civil': {
		'duration': '4 Years',
		'fees': 'Rs. 1,00,000 per year',
		'description': 'Civil engineering basics, structural design, surveying, and site-based learning for future engineers.',
		'highlights': ['Survey labs', 'Structure design', 'Site exposure'],
	},
	'BCA': {
		'duration': '3 Years',
		'fees': 'Rs. 75,000 per year',
		'description': 'A computer applications program focused on programming, databases, networking, and application development.',
		'highlights': ['Programming basics', 'Database skills', 'Application building'],
	},
	'MCA': {
		'duration': '2 Years',
		'fees': 'Rs. 90,000 per year',
		'description': 'Advanced software development program for graduates who want deep application engineering skills.',
		'highlights': ['Advanced software labs', 'System design', 'Project mentoring'],
	},
	'MBA': {
		'duration': '2 Years',
		'fees': 'Rs. 1,50,000 per year',
		'description': 'A management-focused track with strategy, communication, operations, analytics, and leadership modules.',
		'highlights': ['Business case studies', 'Analytics', 'Leadership training'],
	},
	'B.Sc': {
		'duration': '3 Years',
		'fees': 'Rs. 55,000 per year',
		'description': 'Science foundation program with lab work, quantitative reasoning, and specialization options.',
		'highlights': ['Lab sessions', 'Foundation subjects', 'Research exposure'],
	},
	'M.Sc': {
		'duration': '2 Years',
		'fees': 'Rs. 65,000 per year',
		'description': 'Postgraduate science track with advanced theory, projects, and applied research exposure.',
		'highlights': ['Advanced concepts', 'Research projects', 'Mentored learning'],
	},
}


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


def _save_temp_upload(uploaded_file, subfolder):
	file_name = get_valid_filename(uploaded_file.name)
	temp_key = uuid4().hex
	temp_path = f'{TEMP_ADMISSION_FOLDER}/{subfolder}/{temp_key}_{file_name}'
	return default_storage.save(temp_path, uploaded_file)


def _read_temp_file(temp_path, final_name):
	with default_storage.open(temp_path, 'rb') as temp_file:
		return ContentFile(temp_file.read(), name=final_name)


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


def _course_snapshot(course_name):
	return COURSE_CATALOG.get(course_name, {})


def _course_defaults(course_name):
	snapshot = _course_snapshot(course_name)
	duration_text = snapshot.get('duration', '')
	duration_years = 0
	match = re.search(r'(\d+)', duration_text)
	if match:
		duration_years = int(match.group(1))
	level = 'Academic'
	if course_name.startswith('B.Tech') or course_name in ('BCA', 'B.Sc'):
		level = 'Undergraduate'
	elif course_name in ('MCA', 'MBA', 'M.Sc'):
		level = 'Postgraduate'
	return {
		'level': level,
		'duration_years': duration_years,
		'description': snapshot.get('description', ''),
		'status': 'active',
	}


def _generate_local_admission_no():
	base = f"ENR{timezone.now().strftime('%Y%m%d%H%M%S')}"
	for _ in range(20):
		candidate = f"{base}{uuid4().hex[:6].upper()}"
		if not Participant.objects.using('server').filter(admission_no=candidate).exists():
			return candidate
	raise ValueError('Unable to generate a unique admission number.')


def _get_participant_for_user(user):
	if not user.is_authenticated:
		return None
	return Participant.objects.using('server').filter(user_id=user.id).first()


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
		'academic_year': draft.get('academic', {}).get('academic_year', ''),
		'payment': draft.get('payment', {}),
		'documents': draft.get('documents', []),
		'submitted_at': timezone.now().isoformat(),
		'course_snapshot': _course_snapshot(draft.get('course', {}).get('course', '')),
		'session_key': request.session.session_key,
	}


def _finalize_admission(request, draft, receipt_file=None):
	personal = draft.get('personal', {})
	academic = draft.get('academic', {})
	course = draft.get('course', {})
	payment = draft.get('payment', {})
	documents = draft.get('documents', [])

	if User.objects.filter(username=course.get('username')).exists():
		raise ValueError('That username is already taken.')

	user = User.objects.create_user(
		username=course['username'],
		password=course['password1'],
		email=personal.get('email', ''),
		first_name=personal.get('first_name', ''),
		last_name=personal.get('last_name', ''),
	)

	# Resolve or create course record
	course_obj = None
	if course.get('course'):
		course_obj, created = Course.objects.using('server').get_or_create(
			course_name=course['course'],
			defaults=_course_defaults(course['course']),
		)
		if not created:
			updated = False
			for field_name, field_value in _course_defaults(course['course']).items():
				if getattr(course_obj, field_name) != field_value:
					setattr(course_obj, field_name, field_value)
					updated = True
			if updated:
				course_obj.save(using='server')

	admission_no = _generate_local_admission_no()

	participant = Participant.objects.using('server').create(
		user_id=user.id,
		admission_no=admission_no,
		first_name=personal.get('first_name', ''),
		last_name=personal.get('last_name', ''),
		dob=date.fromisoformat(personal['dob']) if personal.get('dob') else None,
		gender=personal.get('gender', ''),
		mobile=personal.get('mobile', ''),
		email=personal.get('email', ''),
		course=course_obj,
		academic_year_id=academic.get('academic_year', ''),
		status='pending',
	)

	guardian_name = personal.get('guardian_name', '').strip()
	if guardian_name:
		ParticipantGuardian.objects.using('server').create(
			participant=participant,
			guardian_name=guardian_name,
			relationship=personal.get('relationship', ''),
			mobile=personal.get('guardian_mobile', ''),
			email=personal.get('guardian_email', ''),
			address=personal.get('guardian_address', ''),
		)

	final_documents = []
	for document in documents:
		stored_name = get_valid_filename(document['original_name'])
		final_path = f'student_documents/{user.username}/{document["document_type"]}_{stored_name}'
		default_storage.save(final_path, _read_temp_file(document['temp_path'], stored_name))
		final_documents.append({
			'document_type': document['document_type'],
			'file_path': final_path,
		})

	receipt_path = payment.get('receipt_path', '')
	if receipt_file is not None:
		stored_receipt_name = get_valid_filename(getattr(receipt_file, 'name', 'receipt'))
		final_receipt_path = f'student_documents/{user.username}/payment_{stored_receipt_name}'
		default_storage.save(final_receipt_path, receipt_file)
		payment['receipt_final_path'] = final_receipt_path
	elif receipt_path:
		stored_receipt_name = get_valid_filename(receipt_path.split('/')[-1])
		final_receipt_path = f'student_documents/{user.username}/payment_{stored_receipt_name}'
		default_storage.save(final_receipt_path, _read_temp_file(receipt_path, stored_receipt_name))
		payment['receipt_final_path'] = final_receipt_path

	manifest = _manifest_for_draft(request, draft)
	manifest['documents'] = final_documents
	manifest_path = f'student_documents/{user.username}/application_summary.json'
	default_storage.save(manifest_path, ContentFile(json.dumps(manifest, indent=2), name='application_summary.json'))

	# Try to obtain/generate an admission_no override from external API if configured.
	def _generate_enrollment_id(user, participant):
		# If API URL provided in settings, call it
		api_url = getattr(settings, 'ENROLLMENT_API_URL', None)
		api_key = getattr(settings, 'ENROLLMENT_API_KEY', None)
		payload = {
			'username': user.username,
			'first_name': user.first_name,
			'last_name': user.last_name,
			'email': user.email,
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

	api_admission_no = _generate_enrollment_id(user, participant)
	if api_admission_no and api_admission_no != participant.admission_no:
		if not Participant.objects.using('server').filter(admission_no=api_admission_no).exists():
			participant.admission_no = api_admission_no
			participant.save(using='server', update_fields=['admission_no'])

	return participant


def landing(request):
	return render(request, 'landing.html')


def register_view(request):
	if request.user.is_authenticated:
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
				draft['personal']['photo_path'] = _save_temp_upload(form.cleaned_data['photo'], _ensure_session_key(request))
			_save_admission_draft(request, draft)
			return redirect('participantmgmt:register_documents')
	else:
		form = PersonalDetailsForm(initial=initial_data)
	return render(request, 'accounts/register_step1.html', {
		'form': form,
	})


def register_documents_view(request):
	if request.user.is_authenticated:
		return redirect('participantmgmt:home')
	draft = _get_admission_draft(request)
	if not draft.get('personal'):
		return redirect('participantmgmt:register')

	academic_form = AcademicDetailsForm(initial=draft.get('academic', {}))
	document_rows = _admission_doc_rows(draft)
	if request.method == 'POST':
		academic_form = AcademicDetailsForm(request.POST)
		documents, incomplete_rows = _extract_document_rows(request.POST, request.FILES)
		if academic_form.is_valid() and not incomplete_rows and documents:
			draft['academic'] = academic_form.cleaned_data
			draft_documents = []
			for document in documents:
				draft_documents.append({
					'document_type': document['document_type'],
					'original_name': document['original_name'],
					'temp_path': _save_temp_upload(document['temp_file'], _ensure_session_key(request)),
				})
			draft['documents'] = draft_documents
			_save_admission_draft(request, draft)
			return redirect('participantmgmt:register_course')
		if not documents:
			academic_form.add_error(None, 'Please upload at least one document.')
		elif incomplete_rows:
			academic_form.add_error(None, 'Each document row must include both a document type and a file.')
		document_rows = _posted_document_rows(request.POST, request.FILES)
	return render(request, 'accounts/register_step2.html', {
		'form': academic_form,
		'document_rows': document_rows,
		'document_choices': DOCUMENT_TYPE_CHOICES,
	})


def register_course_view(request):
	if request.user.is_authenticated:
		return redirect('participantmgmt:home')
	draft = _get_admission_draft(request)
	if not draft.get('personal') or not draft.get('academic') or not draft.get('documents'):
		return redirect('participantmgmt:register')

	form = CourseSelectionForm(initial=draft.get('course', {}))
	if request.method == 'POST':
		form = CourseSelectionForm(request.POST)
		if form.is_valid():
			if User.objects.filter(username=form.cleaned_data['username']).exists():
				form.add_error('username', 'This username is already taken.')
			else:
				draft['course'] = form.cleaned_data
				_save_admission_draft(request, draft)
				return redirect('participantmgmt:register_payment')
	return render(request, 'accounts/register_step3.html', {
		'form': form,
		'course_catalog': COURSE_CATALOG,
	})


def register_payment_view(request):
	if request.user.is_authenticated:
		return redirect('participantmgmt:home')
	draft = _get_admission_draft(request)
	if not draft.get('personal') or not draft.get('academic') or not draft.get('documents') or not draft.get('course'):
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
		'course_summary': _course_snapshot(draft.get('course', {}).get('course', '')),
		'payment_methods': PAYMENT_METHOD_CHOICES,
	})


def login_view(request):
	if request.user.is_authenticated:
		return redirect('participantmgmt:home')
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			user = authenticate(request, username=username, password=password)
			if user:
				if user.is_superuser:
					login(request, user)
					return redirect('/admin/')
				login(request, user)
				return redirect('participantmgmt:home')
			messages.error(request, 'Invalid username or password.')
	else:
		form = LoginForm()
	return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
	logout(request)
	messages.success(request, 'You have been logged out successfully.')
	return redirect('participantmgmt:landing')


@login_required
def home(request):
	participant = _get_participant_for_user(request.user)
	if not participant:
		return redirect('participantmgmt:landing')
	# Attendance, results and notifications tables were removed in the new schema.
	return render(request, 'dashboard/home.html', {
		'student': participant,
		'attendance_pct': 0,
		'recent_attendance': [],
		'recent_results': [],
		'notifications': [],
		'total_subjects': 0,
		'total_attendance_days': 0,
	})


@login_required
def profile_view(request):
	participant = get_object_or_404(Participant.objects.using('server'), user_id=request.user.id)
	return render(request, 'students/profile.html', {'student': participant})


@login_required
def profile_edit(request):
	participant = get_object_or_404(Participant.objects.using('server'), user_id=request.user.id)
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


@login_required
def attendance_view(request):
	participant = get_object_or_404(Participant.objects.using('server'), user_id=request.user.id)
	return render(request, 'students/attendance.html', {
		'student': participant,
		'attendance_records': [],
		'percentage': 0,
		'month_filter': '',
	})


@login_required
def results_view(request):
	participant = get_object_or_404(Participant.objects.using('server'), user_id=request.user.id)
	return render(request, 'students/results.html', {
		'student': participant,
		'results': [],
		'semesters': [],
		'semester_filter': '',
		'overall_pct': 0,
	})