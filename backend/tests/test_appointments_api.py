from datetime import datetime, timedelta

import pytest
from sqlmodel import Session

from app.models import Provider, Slot


@pytest.fixture
def patient_headers(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Patient",
            "email": "patient@example.com",
            "password": "test-password",
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def create_slot(test_db, start_time):
    with Session(test_db) as session:
        provider = Provider(name="Dr. Test", specialty="Primary care")
        session.add(provider)
        session.flush()
        slot = Slot(provider_id=provider.id, start_time=start_time)
        session.add(slot)
        session.commit()
        session.refresh(slot)
        return slot.id


def test_patient_books_and_cancels_appointment(client, patient_headers, test_db):
    slot_id = create_slot(test_db, datetime.now() + timedelta(days=1))
    response = client.post(
        "/api/appointments",
        headers=patient_headers,
        json={"slot_id": slot_id, "reason": "Annual checkup"},
    )

    assert response.status_code == 200
    appointment = response.json()
    assert appointment["slot_id"] == slot_id
    assert appointment["reason"] == "Annual checkup"
    assert appointment["status"] == "confirmed"
    assert client.get("/api/slots").json() == []

    response = client.patch(
        f"/api/appointments/{appointment['id']}/cancel", headers=patient_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert [slot["id"] for slot in client.get("/api/slots").json()] == [slot_id]


def test_patient_cannot_book_an_already_booked_slot(client, patient_headers, test_db):
    slot_id = create_slot(test_db, datetime.now() + timedelta(days=1))
    request = {"headers": patient_headers, "json": {"slot_id": slot_id}}
    assert client.post("/api/appointments", **request).status_code == 200

    response = client.post("/api/appointments", **request)

    assert response.status_code == 400
    assert response.json() == {"detail": "That time is no longer available"}


def test_patient_cannot_book_a_past_slot(client, patient_headers, test_db):
    slot_id = create_slot(test_db, datetime.now() - timedelta(days=1))

    response = client.post(
        "/api/appointments", headers=patient_headers, json={"slot_id": slot_id}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "That time is no longer available"}
