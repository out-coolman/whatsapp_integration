"""
Metrics and analytics API endpoints.
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime, timedelta
import io
import csv
import json

from app.core.database import get_db
from app.api.dependencies import CommonQueryParams
from app.api.v1.auth import get_current_active_user
from app.models.user import User
from app.models.aggregates import (
    LeadFunnelMetrics, TelephonyMetrics, WhatsAppMetrics,
    NoShowMetrics, MetricsCheckpoint
)

router = APIRouter()


@router.get("/metrics/overview")
async def get_overview_metrics(
    date_from: Optional[date] = Query(None, description="Start date for metrics"),
    date_to: Optional[date] = Query(None, description="End date for metrics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get overview metrics including funnel and real-time data."""

    # Check permission
    if not current_user.has_permission("view_dashboard"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view metrics"
        )

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    # Get aggregated funnel metrics
    funnel_metrics = db.query(LeadFunnelMetrics).filter(
        LeadFunnelMetrics.date.between(date_from, date_to)
    ).all()

    # Calculate totals
    total_new = sum(m.leads_new or 0 for m in funnel_metrics)
    total_contacted = sum(m.leads_contacted or 0 for m in funnel_metrics)
    total_qualified = sum(m.leads_qualified or 0 for m in funnel_metrics)
    total_booked = sum(m.leads_booked or 0 for m in funnel_metrics)
    total_showed = sum(m.leads_showed or 0 for m in funnel_metrics)

    # Calculate conversion rates
    contact_rate = (total_contacted / total_new * 100) if total_new > 0 else 0
    qualification_rate = (total_qualified / total_contacted * 100) if total_contacted > 0 else 0
    booking_rate = (total_booked / total_qualified * 100) if total_qualified > 0 else 0
    show_rate = (total_showed / total_booked * 100) if total_booked > 0 else 0

    # Get real-time summary
    realtime_query = text("SELECT * FROM mv_realtime_summary LIMIT 1")
    realtime_result = db.execute(realtime_query).fetchone()

    realtime_data = dict(realtime_result) if realtime_result else {}

    return {
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        },
        "funnel": {
            "leads_new": total_new,
            "leads_contacted": total_contacted,
            "leads_qualified": total_qualified,
            "leads_booked": total_booked,
            "leads_showed": total_showed,
            "contact_rate": round(contact_rate, 2),
            "qualification_rate": round(qualification_rate, 2),
            "booking_rate": round(booking_rate, 2),
            "show_rate": round(show_rate, 2)
        },
        "realtime": realtime_data
    }


@router.get("/metrics/telephony")
async def get_telephony_metrics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get telephony/call metrics."""

    # Check permission
    if not current_user.has_permission("view_dashboard"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view telephony metrics"
        )

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    metrics = db.query(TelephonyMetrics).filter(
        TelephonyMetrics.date.between(date_from, date_to)
    ).all()

    # Aggregate totals
    total_initiated = sum(m.calls_initiated or 0 for m in metrics)
    total_answered = sum(m.calls_answered or 0 for m in metrics)
    total_completed = sum(m.calls_completed or 0 for m in metrics)
    total_talk_time = sum(m.total_talk_time or 0 for m in metrics)
    total_cost_cents = sum(m.total_cost_cents or 0 for m in metrics)

    return {
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        },
        "totals": {
            "calls_initiated": total_initiated,
            "calls_answered": total_answered,
            "calls_completed": total_completed,
            "answer_rate": round((total_answered / total_initiated * 100) if total_initiated > 0 else 0, 2),
            "completion_rate": round((total_completed / total_answered * 100) if total_answered > 0 else 0, 2),
            "total_talk_time_minutes": round(total_talk_time / 60, 1),
            "total_cost_dollars": round(total_cost_cents / 100, 2),
            "avg_cost_per_call": round(total_cost_cents / total_initiated / 100, 2) if total_initiated > 0 else 0
        },
        "daily_breakdown": [
            {
                "date": m.date.isoformat(),
                "calls_initiated": m.calls_initiated,
                "calls_answered": m.calls_answered,
                "answer_rate": float(m.answer_rate or 0) * 100,
                "avg_talk_time_minutes": round((m.avg_talk_time or 0) / 60, 1)
            }
            for m in metrics
        ]
    }


@router.get("/metrics/whatsapp")
async def get_whatsapp_metrics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get WhatsApp messaging metrics."""

    # Check permission
    if not current_user.has_permission("view_dashboard"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view WhatsApp metrics"
        )

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    metrics = db.query(WhatsAppMetrics).filter(
        WhatsAppMetrics.date.between(date_from, date_to)
    ).all()

    total_sent = sum(m.messages_sent or 0 for m in metrics)
    total_delivered = sum(m.messages_delivered or 0 for m in metrics)
    total_read = sum(m.messages_read or 0 for m in metrics)
    total_received = sum(m.messages_received or 0 for m in metrics)

    return {
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        },
        "totals": {
            "messages_sent": total_sent,
            "messages_delivered": total_delivered,
            "messages_read": total_read,
            "messages_received": total_received,
            "delivery_rate": round((total_delivered / total_sent * 100) if total_sent > 0 else 0, 2),
            "read_rate": round((total_read / total_delivered * 100) if total_delivered > 0 else 0, 2),
            "response_rate": round((total_received / total_sent * 100) if total_sent > 0 else 0, 2)
        }
    }


@router.get("/metrics/no_shows")
async def get_no_show_metrics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    professional_id: Optional[str] = Query(None),
    clinic_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get no-show metrics and forecasting."""

    # Check permission
    if not current_user.has_permission("view_dashboard"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view no-show metrics"
        )

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    query = db.query(NoShowMetrics).filter(
        NoShowMetrics.date.between(date_from, date_to)
    )

    if professional_id:
        query = query.filter(NoShowMetrics.professional_id == professional_id)
    if clinic_id:
        query = query.filter(NoShowMetrics.clinic_id == clinic_id)

    metrics = query.all()

    total_scheduled = sum(m.appointments_scheduled or 0 for m in metrics)
    total_no_shows = sum(m.appointments_no_show or 0 for m in metrics)
    total_completed = sum(m.appointments_completed or 0 for m in metrics)

    return {
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        },
        "totals": {
            "appointments_scheduled": total_scheduled,
            "appointments_no_show": total_no_shows,
            "appointments_completed": total_completed,
            "no_show_rate": round((total_no_shows / total_scheduled * 100) if total_scheduled > 0 else 0, 2)
        },
        "breakdown": [
            {
                "date": m.date.isoformat(),
                "professional_id": m.professional_id,
                "professional_name": m.professional_name,
                "clinic_name": m.clinic_name,
                "no_show_rate": float(m.no_show_rate or 0) * 100,
                "risk_score": float(m.risk_score or 0)
            }
            for m in metrics
        ]
    }


@router.get("/export/metrics.csv")
async def export_metrics_csv(
    metric_type: str = Query(..., description="Type of metrics to export"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export metrics as CSV file."""

    # Check permission
    if not current_user.has_permission("export_data"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to export metrics"
        )

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    # Determine which metrics to export
    if metric_type == "funnel":
        metrics = db.query(LeadFunnelMetrics).filter(
            LeadFunnelMetrics.date.between(date_from, date_to)
        ).all()
        fieldnames = ['date', 'leads_new', 'leads_contacted', 'leads_qualified',
                     'leads_booked', 'leads_showed', 'contact_rate', 'booking_rate']
    elif metric_type == "telephony":
        metrics = db.query(TelephonyMetrics).filter(
            TelephonyMetrics.date.between(date_from, date_to)
        ).all()
        fieldnames = ['date', 'calls_initiated', 'calls_answered', 'calls_completed',
                     'answer_rate', 'avg_talk_time', 'total_cost_cents']
    else:
        raise HTTPException(status_code=400, detail="Invalid metric type")

    # Generate CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for metric in metrics:
        row = {field: getattr(metric, field) for field in fieldnames}
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={metric_type}_metrics.csv"}
    )