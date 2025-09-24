"""
Tests for Helena CRM webhook endpoints.
"""
import pytest
from fastapi import status

from app.models.lead import Lead
from app.models.event import Event


def test_helena_webhook_lead_created(client, db_session, sample_webhook_payload, api_headers):
    """Test Helena webhook for lead creation."""
    response = client.post(
        "/api/v1/webhooks/helena",
        json=sample_webhook_payload,
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert "event_id" in data
    assert "correlation_id" in data

    # Verify lead was created
    lead = db_session.query(Lead).filter_by(helena_id="test_lead_123").first()
    assert lead is not None
    assert lead.first_name == "João"
    assert lead.last_name == "Silva"
    assert lead.phone == "+5563991234567"

    # Verify event was created
    event = db_session.query(Event).filter_by(id=data["event_id"]).first()
    assert event is not None
    assert event.event_type.value == "lead_created"
    assert event.lead_id == lead.id


def test_helena_webhook_duplicate_event(client, db_session, sample_webhook_payload, api_headers):
    """Test Helena webhook handles duplicate events."""
    # Add idempotency key
    sample_webhook_payload["idempotency_key"] = "test_unique_key_123"

    # First request
    response1 = client.post(
        "/api/v1/webhooks/helena",
        json=sample_webhook_payload,
        headers=api_headers
    )
    assert response1.status_code == status.HTTP_200_OK

    # Second request with same idempotency key
    response2 = client.post(
        "/api/v1/webhooks/helena",
        json=sample_webhook_payload,
        headers=api_headers
    )
    assert response2.status_code == status.HTTP_200_OK
    data = response2.json()
    assert "already processed" in data["message"].lower()


def test_helena_webhook_unauthorized(client, sample_webhook_payload):
    """Test Helena webhook without API key."""
    response = client.post(
        "/api/v1/webhooks/helena",
        json=sample_webhook_payload
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_helena_webhook_invalid_payload(client, api_headers):
    """Test Helena webhook with invalid payload."""
    invalid_payload = {
        "event_type": "lead_created",
        # Missing required fields
    }

    response = client.post(
        "/api/v1/webhooks/helena",
        json=invalid_payload,
        headers=api_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_helena_webhook_test_endpoint(client):
    """Test Helena webhook test endpoint."""
    response = client.get("/api/v1/webhooks/helena/test")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"