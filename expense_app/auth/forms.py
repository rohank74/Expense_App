import re
from dataclasses import dataclass


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class FormValidationError(ValueError):
    pass


@dataclass(frozen=True)
class RegistrationData:
    name: str
    email: str
    password: str


@dataclass(frozen=True)
class LoginData:
    email: str
    password: str


def parse_registration_form(form):
    name = form.get("name", "").strip()
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")
    confirm_password = form.get("confirm_password", "")

    if not name:
        raise FormValidationError("Name is required.")
    if not email:
        raise FormValidationError("Email is required.")
    if not password:
        raise FormValidationError("Password is required.")
    if not confirm_password:
        raise FormValidationError("Please confirm your password.")
    if EMAIL_PATTERN.match(email) is None:
        raise FormValidationError("Please enter a valid email address.")
    if password != confirm_password:
        raise FormValidationError("Passwords do not match.")

    return RegistrationData(name=name, email=email, password=password)


def parse_login_form(form):
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")

    if not email or not password:
        raise FormValidationError("Email and password are required.")

    return LoginData(email=email, password=password)
