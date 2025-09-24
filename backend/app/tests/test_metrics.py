"""
Tests for metrics API endpoints.
"""
import pytest
from datetime import date, timedelta
from fastapi import status

from app.models.aggregates import LeadFunnelMetrics, TelephonyMetrics


def test_get_overview_metrics(client, api_headers):
    """Test getting overview metrics."""
    response = client.get(
        "/api/v1/metrics/overview",
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "period" in data
    assert "funnel" in data
    assert "realtime" in data

    # Check funnel structure
    funnel = data["funnel"]
    assert "leads_new" in funnel
    assert "leads_contacted" in funnel
    assert "contact_rate" in funnel


def test_get_telephony_metrics(client, api_headers):
    """Test getting telephony metrics."""
    response = client.get(
        "/api/v1/metrics/telephony",
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "period" in data
    assert "totals" in data
    assert "daily_breakdown" in data

    # Check totals structure
    totals = data["totals"]
    assert "calls_initiated" in totals
    assert "answer_rate" in totals


def test_get_whatsapp_metrics(client, api_headers):
    """Test getting WhatsApp metrics."""
    response = client.get(
        "/api/v1/metrics/whatsapp",
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "period" in data
    assert "totals" in data

    # Check totals structure
    totals = data["totals"]
    assert "messages_sent" in totals
    assert "delivery_rate" in totals


def test_get_no_show_metrics(client, api_headers):
    """Test getting no-show metrics."""
    response = client.get(
        "/api/v1/metrics/no_shows",
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "period" in data
    assert "totals" in data
    assert "breakdown" in data


def test_metrics_with_date_range(client, api_headers):
    """Test metrics with custom date range."""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    response = client.get(
        "/api/v1/metrics/overview",
        params={
            "date_from": start_date.isoformat(),
            "date_to": end_date.isoformat()
        },
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["period"]["from"] == start_date.isoformat()
    assert data["period"]["to"] == end_date.isoformat()


def test_export_metrics_csv(client, api_headers):
    """Test CSV export of metrics."""
    response = client.get(
        "/api/v1/export/metrics.csv",
        params={"metric_type": "funnel"},
        headers=api_headers
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers.get("content-disposition", "")


def test_export_invalid_metric_type(client, api_headers):
    """Test CSV export with invalid metric type."""
    response = client.get(
        "/api/v1/export/metrics.csv",
        params={"metric_type": "invalid"},
        headers=api_headers
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_metrics_unauthorized(client):
    """Test metrics endpoints without authentication."""
    response = client.get("/api/v1/metrics/overview")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.get("/api/v1/metrics/telephony")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.get("/api/v1/export/metrics.csv", params={"metric_type": "funnel"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED