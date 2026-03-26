import re
from datetime import date

from models import ClientWork, Lead


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^[0-9+\-\s()]{7,20}$")


def clean_text(value):
    return value.strip() if value else ""


def normalize_email(value):
    return clean_text(value).lower()


def validate_required_text(value, field_name):
    cleaned_value = clean_text(value)
    if not cleaned_value:
        return None, f"{field_name} is required."
    return cleaned_value, None


def validate_email(value):
    email = normalize_email(value)
    if not email:
        return None, "Email is required."
    if not EMAIL_PATTERN.match(email):
        return None, "Enter a valid email address."
    return email, None


def validate_password(value):
    password = clean_text(value)
    if not password:
        return None, "Password is required."
    if len(password) < 6:
        return None, "Password must be at least 6 characters long."
    return password, None


def validate_login_password(value):
    password = clean_text(value)
    if not password:
        return None, "Password is required."
    return password, None


def validate_phone(value):
    phone = clean_text(value)
    if not phone:
        return None, "Phone is required."
    if not PHONE_PATTERN.match(phone):
        return None, "Enter a valid phone number."
    return phone, None


def validate_service(value):
    service = clean_text(value)
    if service not in Lead.SERVICE_OPTIONS:
        return None, "Please select a valid service."
    return service, None


def validate_optional_text(value):
    return clean_text(value), None


def validate_status(value):
    status = clean_text(value)
    if status not in Lead.VALID_STATUS_OPTIONS:
        return None, "Invalid status selected."
    return status, None


def validate_progress_status(value):
    progress_status = clean_text(value)
    if progress_status not in ClientWork.PROGRESS_OPTIONS:
        return None, "Please select a valid progress status."
    return progress_status, None


def validate_date(value, field_name, required=True):
    cleaned_value = clean_text(value)
    if not cleaned_value:
        if required:
            return None, f"{field_name} is required."
        return None, None

    try:
        return date.fromisoformat(cleaned_value), None
    except ValueError:
        return None, f"Enter a valid date for {field_name}."


def validate_date_range(start_date, end_date):
    if start_date and end_date and end_date < start_date:
        return "End date cannot be before start date."
    return None
