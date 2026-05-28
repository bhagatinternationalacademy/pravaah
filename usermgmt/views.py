from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group

from .models import User, AuditLog
from commonservices.utils import send_email, get_client_ip


def _redirect_if_session_expired(request):
	if not request.user.is_authenticated:
		return redirect('usermgmt:session_expired')
	return None

# Create your views here.

def login_view(request):
	# Handle login form POST and render login template
	if request.method == 'POST':
		username_input = request.POST.get('username', '').strip()
		password = request.POST.get('password', '')
		remember = request.POST.get('remember')

		# simple brute-force protection per-session
		failures = request.session.get('login_failures', {})
		entry = failures.get(username_input, {'count': 0, 'first': None})
		first_ts = entry.get('first')
		if first_ts and entry.get('count', 0) >= 5 and (timezone.now().timestamp() - first_ts) < 15 * 60:
			messages.error(request, 'Too many failed login attempts. Try again later.')
			return render(request, 'auth/login.html')

		# allow login by email: lookup username if input looks like email
		username = username_input
		if '@' in username_input:
			try:
				u = User.objects.get(email__iexact=username_input)
				username = u.username
			except User.DoesNotExist:
				username = username_input

		user = authenticate(request, username=username, password=password)
		if user is not None:
			if not user.is_active:
				messages.error(request, 'Account inactive. Please verify your email or contact support.')
				return render(request, 'auth/login.html')
			if not user.is_email_verified:
				messages.error(request, 'Email not verified. Please check your inbox or resend verification.')
				return render(request, 'auth/login.html')

			login(request, user)
			# session expiry handling
			if remember:
				request.session.set_expiry(1209600)  # 2 weeks
			else:
				request.session.set_expiry(0)  # browser close

			# audit log
			AuditLog.objects.create(user=user, action='Login Success', ip_address=get_client_ip(request), browser_agent=request.META.get('HTTP_USER_AGENT', ''))

			# reset failures
			if username_input in failures:
				failures.pop(username_input)
				request.session['login_failures'] = failures

			# simple role-based redirect (customize as needed)
			groups = list(user.groups.values_list('name', flat=True))
			if user.is_superuser or 'Super Admin' in groups or 'System Admin' in groups:
				return redirect('usermgmt:admin_dashboard')
			return redirect('usermgmt:admin_dashboard')
		else:
			# increment failure count
			entry['count'] = entry.get('count', 0) + 1
			if not entry.get('first'):
				entry['first'] = timezone.now().timestamp()
			failures[username_input] = entry
			request.session['login_failures'] = failures
			# audit
			AuditLog.objects.create(user=None, action=f'Login Failed for {username_input}', ip_address=get_client_ip(request), browser_agent=request.META.get('HTTP_USER_AGENT', ''))
			messages.error(request, 'Invalid username or password')

	return render(request, 'auth/login.html')

def register_view(request):
	if request.method == 'POST':
		first_name = request.POST.get('first_name', '').strip()
		last_name = request.POST.get('last_name', '').strip()
		username = request.POST.get('username', '').strip()
		email = request.POST.get('email', '').strip()
		mobile = request.POST.get('mobile', '').strip() or request.POST.get('mobile_number', '').strip()
		role = request.POST.get('role', '').strip()
		password = request.POST.get('password', '')
		confirm_password = request.POST.get('confirm_password', '')

		if not all([first_name, last_name, username, email, password, confirm_password]):
			messages.error(request, 'Please fill in all required fields.')
			return render(request, 'auth/register.html')

		if password != confirm_password:
			messages.error(request, 'Passwords do not match.')
			return render(request, 'auth/register.html')

		# password strength
		try:
			validate_password(password)
		except ValidationError as e:
			messages.error(request, ' '.join(e.messages))
			return render(request, 'auth/register.html')

		# create user atomically
		try:
			with transaction.atomic():
				if User.objects.filter(username=username).exists():
					messages.error(request, 'Username already exists.')
					return render(request, 'auth/register.html')
				if User.objects.filter(email=email).exists():
					messages.error(request, 'Email already exists.')
					return render(request, 'auth/register.html')

				user = User.objects.create_user(
					username=username,
					email=email,
					password=password,
					first_name=first_name,
					last_name=last_name,
				)
				user.mobile = mobile
				user.is_active = False
				user.is_email_verified = False
				user.save()

				# assign group if exists
				if role:
					try:
						grp = Group.objects.get(name=role)
						user.groups.add(grp)
					except Group.DoesNotExist:
						pass

				# generate and persist token
				uid = urlsafe_base64_encode(force_bytes(user.pk))
				token = default_token_generator.make_token(user)
				user.email_verification_token = token
				user.token_created_at = timezone.now()
				user.save(update_fields=['email_verification_token', 'token_created_at'])

				# audit and send verification email (hand off to email service)
				verify_link = request.build_absolute_uri(reverse('usermgmt:verify_email_confirm', args=[uid, token]))
				AuditLog.objects.create(user=user, action='User Registered', ip_address=get_client_ip(request), browser_agent=request.META.get('HTTP_USER_AGENT', ''))
				try:
					send_email(to=user.email, subject='Verify your account', template='verify_email', context={'first_name': user.first_name, 'username': user.username, 'verify_link': verify_link})
					AuditLog.objects.create(user=user, action='Verification Email Sent', ip_address=get_client_ip(request))
				except Exception:
					# fallback: still show generic message
					AuditLog.objects.create(user=user, action='Verification Email Enqueue Failed', ip_address=get_client_ip(request))

				messages.success(request, 'Account created. Check your email for verification instructions.')
				return redirect('usermgmt:verify_email')

		except IntegrityError:
			messages.error(request, 'A user with that username or email already exists.')
			return render(request, 'auth/register.html')

	return render(request, 'auth/register.html')

def forgot_password_view(request):
	if request.method == 'POST':
		email = request.POST.get('email')
		# Always show generic message to avoid account enumeration
		messages.success(request, 'If an account with that email exists, a password reset link has been sent.')
		if not email:
			return render(request, 'auth/forgot_password.html')

		try:
			user = User.objects.get(email__iexact=email)
		except User.DoesNotExist:
			return render(request, 'auth/forgot_password.html')

		# throttle: do not send too frequently
		last = user.token_created_at
		if last and (timezone.now() - last).total_seconds() < 60:
			return render(request, 'auth/forgot_password.html')

		uid = urlsafe_base64_encode(force_bytes(user.pk))
		token = default_token_generator.make_token(user)
		# persist token timestamp
		user.email_verification_token = token
		user.token_created_at = timezone.now()
		user.save(update_fields=['email_verification_token', 'token_created_at'])

		reset_link = request.build_absolute_uri(reverse('usermgmt:reset_password_confirm', args=[uid, token]))
		try:
			send_email(to=user.email, subject='Reset your password', template='password_reset_link', context={'reset_link': reset_link})
			AuditLog.objects.create(user=user, action='Password Reset Requested', ip_address=get_client_ip(request))
		except Exception:
			AuditLog.objects.create(user=user, action='Password Reset Enqueue Failed', ip_address=get_client_ip(request))

		return render(request, 'auth/forgot_password.html')
	return render(request, 'auth/forgot_password.html')

def reset_password_view(request):
	messages.info(request, 'Password reset now uses a secure email link. Request a new reset link below.')
	return redirect('usermgmt:forgot_password')


def reset_password_confirm(request, uidb64=None, token=None):
	if not uidb64 or not token:
		messages.error(request, 'Invalid password reset link.')
		return redirect('usermgmt:forgot_password')
	try:
		uid = force_str(urlsafe_base64_decode(uidb64))
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist):
		messages.error(request, 'Invalid password reset link.')
		return redirect('usermgmt:forgot_password')

	if not default_token_generator.check_token(user, token):
		messages.error(request, 'Password reset link is invalid or expired. Please request a new one.')
		return redirect('usermgmt:forgot_password')

	if request.method == 'POST':
		new_password = request.POST.get('new_password')
		confirm_password = request.POST.get('confirm_password')
		if not new_password or new_password != confirm_password:
			messages.error(request, 'Please provide matching passwords.')
			return render(request, 'auth/reset_password_confirm.html')
		try:
			validate_password(new_password)
		except ValidationError as e:
			messages.error(request, ' '.join(e.messages))
			return render(request, 'auth/reset_password_confirm.html')

		user.set_password(new_password)
		user.email_verification_token = ''
		user.token_created_at = None
		user.save(update_fields=['password', 'email_verification_token', 'token_created_at'])
		AuditLog.objects.create(user=user, action='Password Reset Completed', ip_address=get_client_ip(request))
		messages.success(request, 'Password reset successfully. You can now login.')
		return redirect('usermgmt:login')

	return render(request, 'auth/reset_password_confirm.html')

def change_password_view(request):
	from django.contrib.auth.decorators import login_required

	@login_required
	def _inner(request):
		if request.method == 'POST':
			current_password = request.POST.get('current_password')
			new_password = request.POST.get('new_password')
			confirm_password = request.POST.get('confirm_password')
			if not request.user.check_password(current_password):
				messages.error(request, 'Current password is incorrect.')
				return render(request, 'auth/change_password.html')
			if not new_password or new_password != confirm_password:
				messages.error(request, 'Please provide matching new passwords.')
				return render(request, 'auth/change_password.html')
			try:
				validate_password(new_password, user=request.user)
			except ValidationError as e:
				messages.error(request, ' '.join(e.messages))
				return render(request, 'auth/change_password.html')

			request.user.set_password(new_password)
			request.user.save()
			AuditLog.objects.create(user=request.user, action='Password Changed', ip_address=get_client_ip(request))
			messages.success(request, 'Password changed successfully. Please login again.')
			return redirect('usermgmt:login')
		return render(request, 'auth/change_password.html')

	return _inner(request)

def session_expired_view(request):
	return render(request, 'auth/session_expired.html')

def verify_email_view(request, uidb64=None, token=None):
	if uidb64 and token:
		try:
			uid = force_str(urlsafe_base64_decode(uidb64))
			user = User.objects.get(pk=uid)
		except (TypeError, ValueError, OverflowError, User.DoesNotExist):
			messages.error(request, 'Invalid verification link.')
			return redirect('usermgmt:verify_email')

		if default_token_generator.check_token(user, token):
			user.is_active = True
			user.is_email_verified = True
			user.email_verification_token = ''
			user.token_created_at = None
			user.save(update_fields=['is_active', 'is_email_verified', 'email_verification_token', 'token_created_at'])
			AuditLog.objects.create(user=user, action='Email Verified', ip_address=get_client_ip(request))
			messages.success(request, 'Email verified successfully. You can now login.')
			return redirect('usermgmt:login')

		messages.error(request, 'Verification link is invalid or expired.')
		return redirect('usermgmt:verify_email')

	# resend verification
	if request.method == 'POST':
		email = request.POST.get('email')
		if not email:
			messages.error(request, 'Please provide your email to resend verification.')
			return render(request, 'auth/verify_email.html')
		try:
			user = User.objects.get(email__iexact=email)
		except User.DoesNotExist:
			messages.error(request, 'No account found for that email.')
			return render(request, 'auth/verify_email.html')

		# throttle: allow resend every 60 seconds
		last = user.token_created_at
		if last and (timezone.now() - last).total_seconds() < 60:
			messages.error(request, 'Please wait before requesting another verification email.')
			return render(request, 'auth/verify_email.html')

		token = default_token_generator.make_token(user)
		user.email_verification_token = token
		user.token_created_at = timezone.now()
		user.save(update_fields=['email_verification_token', 'token_created_at'])
		uid = urlsafe_base64_encode(force_bytes(user.pk))
		verify_link = request.build_absolute_uri(reverse('usermgmt:verify_email_confirm', args=[uid, token]))
		try:
			send_email(to=user.email, subject='Verify your account', template='verify_email', context={'first_name': user.first_name, 'username': user.username, 'verify_link': verify_link})
			AuditLog.objects.create(user=user, action='Verification Email Sent (resend)', ip_address=get_client_ip(request))
			messages.success(request, 'Verification email resent. Check your inbox.')
		except Exception:
			AuditLog.objects.create(user=user, action='Verification Email Enqueue Failed (resend)', ip_address=get_client_ip(request))
			messages.error(request, 'Unable to send verification email right now.')

	return render(request, 'auth/verify_email.html')

def logout_view(request):
	user = request.user if request.user.is_authenticated else None
	logout(request)
	if user:
		AuditLog.objects.create(user=user, action='Logout', ip_address=get_client_ip(request))
	messages.success(request, 'You have been logged out.')
	return redirect('usermgmt:login')

def admin_dashboard_view(request):
	redirect_response = _redirect_if_session_expired(request)
	if redirect_response:
		return redirect_response
	return render(request, 'rbac/admin_dashboard.html')

def roles_list_view(request):
	redirect_response = _redirect_if_session_expired(request)
	if redirect_response:
		return redirect_response
	return render(request, 'rbac/roles_list.html')

def role_form_view(request):
	redirect_response = _redirect_if_session_expired(request)
	if redirect_response:
		return redirect_response
	return render(request, 'rbac/role_form.html')

def permissions_list_view(request):
	redirect_response = _redirect_if_session_expired(request)
	if redirect_response:
		return redirect_response
	return render(request, 'rbac/permissions_list.html')

def assign_role_view(request):
	redirect_response = _redirect_if_session_expired(request)
	if redirect_response:
		return redirect_response
	return render(request, 'rbac/assign_role.html')

def assign_permissions_view(request):
	redirect_response = _redirect_if_session_expired(request)
	if redirect_response:
		return redirect_response
	return render(request, 'rbac/assign_permissions.html')

def permission_matrix_view(request):
	redirect_response = _redirect_if_session_expired(request)
	if redirect_response:
		return redirect_response
	return render(request, 'rbac/permission_matrix.html')
