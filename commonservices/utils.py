import random
import uuid

def generate_otp():
    """Generates a 6-digit random verification code as a string."""
    return str(random.randint(100000, 999999))

def generate_uuid():
    """Generates a random UUID string."""
    return str(uuid.uuid4())

def build_verification_link(host, uidb64, token):
    """Constructs user account email verification address link."""
    return f"http://{host}/verify-email/{uidb64}/{token}/"

def build_reset_link(host, uidb64, token):
    """Constructs password reset validation address link."""
    return f"http://{host}/reset-password/{uidb64}/{token}/"

def format_datetime(dt, fmt="%Y-%m-%d %H:%M:%S"):
    """Formats datetime object safely or returns empty string if null."""
    if not dt:
        return ""
    if isinstance(dt, str):
        return dt
    return dt.strftime(fmt)
