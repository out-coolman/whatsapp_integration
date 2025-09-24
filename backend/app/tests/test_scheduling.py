"""
Tests for scheduling API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from fastapi import status

from app.models.lead import Lead
from app.models.appointment import Appointment


@pytest.fixture
def test_lead(db_session, sample_lead_data):
    """Create a test lead."""
    lead = Lead(**sample_lead_data)
    db_session.add(lead)
    db_session.commit()
    return lead


def test_get_availability(client, api_headers):
    """Test getting availability for a professional."""
    response = client.get(
        "/api/v1/availability",
        params={
            "professional_id": "prof_123",
            "date": "2024-12-01",
            "appointment_type": "consultation"
        },
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Should return mock availability data


def test_book_appointment(client, db_session, test_lead, api_headers):
    """Test booking an appointment."""
    future_date = datetime.utcnow() + timedelta(days=7)
    booking_data = {
        "lead_id": test_lead.id,
        "professional_id": "prof_123",
        "scheduled_date": future_date.isoformat(),
        "duration_minutes": 30,
        "appointment_type": "consultation",
        "notes": "Initial consultation"
    }

    response = client.post(
        "/api/v1/schedule",
        json=booking_data,
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert data["lead_id"] == test_lead.id
    assert data["professional_id"] == "prof_123"

    # Verify appointment was created in database
    appointment = db_session.query(Appointment).filter_by(id=data["id"]).first()
    assert appointment is not None
    assert appointment.lead_id == test_lead.id


def test_book_appointment_invalid_lead(client, api_headers):
    """Test booking appointment with invalid lead ID."""
    future_date = datetime.utcnow() + timedelta(days=7)
    booking_data = {
        "lead_id": "invalid_lead_id",
        "professional_id": "prof_123",
        "scheduled_date": future_date.isoformat(),
        "duration_minutes": 30
    }

    response = client.post(
        "/api/v1/schedule",
        json=booking_data,
        headers=api_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_book_appointment_past_date(client, test_lead, api_headers):
    """Test booking appointment in the past."""
    past_date = datetime.utcnow() - timedelta(days=1)
    booking_data = {
        "lead_id": test_lead.id,
        "professional_id": "prof_123",
        "scheduled_date": past_date.isoformat(),
        "duration_minutes": 30
    }

    response = client.post(
        "/api/v1/schedule",
        json=booking_data,
        headers=api_headers
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_appointments(client, api_headers):
    """Test listing appointments."""
    response = client.get(
        "/api/v1/appointments",
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "appointments" in data
    assert "pagination" in data


def test_get_appointment(client, db_session, test_lead, api_headers):
    """Test getting a specific appointment."""
    # Create test appointment
    appointment = Appointment(
        lead_id=test_lead.id,
        scheduled_date=datetime.utcnow() + timedelta(days=7),
        professional_id="prof_123",
        clinic_id="clinic_123"
    )
    db_session.add(appointment)
    db_session.commit()

    response = client.get(
        f"/api/v1/appointments/{appointment.id}",
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == appointment.id
    assert data["lead_id"] == test_lead.id


def test_update_appointment(client, db_session, test_lead, api_headers):
    """Test updating an appointment."""
    # Create test appointment
    appointment = Appointment(
        lead_id=test_lead.id,
        scheduled_date=datetime.utcnow() + timedelta(days=7),
        professional_id="prof_123",
        clinic_id="clinic_123"
    )
    db_session.add(appointment)
    db_session.commit()

    update_data = {
        "status": "confirmed",
        "notes": "Confirmed by patient"
    }

    response = client.put(
        f"/api/v1/appointments/{appointment.id}",
        json=update_data,
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["notes"] == "Confirmed by patient"


def test_scheduling_unauthorized(client, test_lead):
    """Test scheduling endpoints without authentication."""
    response = client.get("/api/v1/availability")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/api/v1/schedule", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.get("/api/v1/appointments")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED