import pytest


def registration(client, **changes):
    data = dict(full_name=" Franck ", email=" Franck@Example.com ", password="123456")
    data.update(changes)
    return client.post("/api/auth/register", json=data)


def test_fr01_registration_then_fr02_login(client):
    response = registration(client)
    assert response.status_code == 200
    assert response.json()["user"]["full_name"] == "Franck"
    assert response.json()["user"]["email"] == "franck@example.com"
    assert "password_hash" not in response.json()["user"]
    login = client.post("/api/auth/login", json={"email": "franck@example.com", "password": "123456"})
    assert login.status_code == 200
    assert login.json()["token"]


def test_fr01_duplicate_normalized_email(client):
    assert registration(client).status_code == 200
    response = registration(client, email="FRANCK@example.com")
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}


@pytest.mark.parametrize("changes,detail", [
    ({"full_name": " "}, "Full name is required"),
    ({"email": "invalid"}, "Enter a valid email address"),
    ({"password": "12345"}, "Password must be at least 6 characters"),
])
def test_fr01_invalid_registration(client, changes, detail):
    response = registration(client, **changes)
    assert response.status_code == 400
    assert response.json() == {"detail": detail}


def test_fr13_patient_cannot_access_admin_stats(client):
    token = registration(client).json()["token"]
    response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}
