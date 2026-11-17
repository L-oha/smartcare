"""Registration rules shared by the API and unit tests."""
import re


def normalize_registration(full_name: str, email: str, password: str) -> tuple[str, str]:
    name = full_name.strip()
    address = email.strip().lower()
    if not name:
        raise ValueError("Full name is required")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", address):
        raise ValueError("Enter a valid email address")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    return name, address
