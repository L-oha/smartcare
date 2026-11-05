import pytest
from app.validation import normalize_registration


@pytest.mark.parametrize("name,email,password,expected", [
    ("Franck", "franck@example.com", "123456", ("Franck", "franck@example.com")),
    (" Franck ", "franck@example.com", "123456", ("Franck", "franck@example.com")),
    ("Franck", "FRANCK@EXAMPLE.COM", "123456", ("Franck", "franck@example.com")),
    ("Franck", " franck@example.com ", "123456", ("Franck", "franck@example.com")),
    ("Franck", "franck@example.com", "1234567", ("Franck", "franck@example.com")),
])
def test_fr01_normalizes_valid_registration(name, email, password, expected):
    assert normalize_registration(name, email, password) == expected


@pytest.mark.parametrize("name,email,password,message", [
    ("", "franck@example.com", "123456", "Full name is required"),
    ("   ", "franck@example.com", "123456", "Full name is required"),
    ("Franck", "franck", "123456", "Enter a valid email address"),
    ("Franck", "a@@example.com", "123456", "Enter a valid email address"),
    ("Franck", "a b@example.com", "123456", "Enter a valid email address"),
    ("Franck", "a@", "123456", "Enter a valid email address"),
    ("Franck", "franck@example.com", "12345", "Password must be at least 6 characters"),
])
def test_fr01_rejects_invalid_registration(name, email, password, message):
    with pytest.raises(ValueError, match=message):
        normalize_registration(name, email, password)
