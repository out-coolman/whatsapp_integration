"""
Leads and CRM management API endpoints.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.models.lead import Lead, LeadStage, LeadSource, LeadClassification
from app.models.user import User
from pydantic import BaseModel, Field

router = APIRouter()


class LeadResponse(BaseModel):
    """Lead response model for API."""
    id: str
    helena_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    stage: str
    classification: str
    source: str
    tags: List[str] = []
    notes: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_contacted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_lead(cls, lead: Lead) -> 'LeadResponse':
        return cls(
            id=lead.id,
            helena_id=lead.helena_id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            full_name=lead.full_name,
            email=lead.email,
            phone=lead.phone,
            stage=lead.stage.value if lead.stage else 'new',
            classification=lead.classification.value if lead.classification else 'cold',
            source=lead.source.value if lead.source else 'other',
            tags=lead.tags or [],
            notes=lead.notes,
            assigned_agent_id=lead.assigned_agent_id,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
            last_contacted_at=lead.last_contacted_at
        )


class CreateLeadRequest(BaseModel):
    """Request model for creating a new lead."""
    first_name: str = Field(..., description="Lead's first name")
    last_name: str = Field(..., description="Lead's last name")
    email: Optional[str] = Field(None, description="Lead's email address")
    phone: Optional[str] = Field(None, description="Lead's phone number")
    notes: Optional[str] = Field(None, description="Additional notes")
    assigned_agent_id: Optional[str] = Field(None, description="ID of assigned agent")
    tags: Optional[List[str]] = Field(default_factory=list, description="Lead tags")
    source: Optional[str] = Field("manual", description="Lead source")


class UpdateLeadRequest(BaseModel):
    """Request model for updating a lead."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    stage: Optional[str] = None
    classification: Optional[str] = None
    notes: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    stage: Optional[str] = Query(None, description="Filter by stage"),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    assigned_agent: Optional[str] = Query(None, description="Filter by assigned agent"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[LeadResponse]:
    """Get all leads with optional filtering."""

    # Check permission
    if not current_user.has_permission("view_leads"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view leads"
        )

    query = db.query(Lead)

    if stage:
        try:
            query = query.filter(Lead.stage == LeadStage(stage.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    if classification:
        try:
            query = query.filter(Lead.classification == LeadClassification(classification.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid classification: {classification}")

    if assigned_agent:
        query = query.filter(Lead.assigned_agent_id == assigned_agent)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Lead.first_name.ilike(search_term)) |
            (Lead.last_name.ilike(search_term)) |
            (Lead.email.ilike(search_term)) |
            (Lead.phone.ilike(search_term))
        )

    leads = query.order_by(Lead.updated_at.desc()).offset(offset).limit(limit).all()
    return [LeadResponse.from_lead(lead) for lead in leads]


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> LeadResponse:
    """Get a specific lead by ID."""

    # Check permission
    if not current_user.has_permission("view_leads"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view leads"
        )

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return LeadResponse.from_lead(lead)


@router.post("/leads", response_model=LeadResponse)
async def create_lead(
    lead_data: CreateLeadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> LeadResponse:
    """Create a new lead."""

    # Check permission
    if not current_user.has_permission("create_leads"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create leads"
        )

    # Check for duplicate email or phone
    if lead_data.email:
        existing_lead = db.query(Lead).filter(Lead.email == lead_data.email).first()
        if existing_lead:
            raise HTTPException(status_code=400, detail="Lead with this email already exists")

    if lead_data.phone:
        existing_lead = db.query(Lead).filter(Lead.phone == lead_data.phone).first()
        if existing_lead:
            raise HTTPException(status_code=400, detail="Lead with this phone number already exists")

    # Create new lead
    lead = Lead(
        first_name=lead_data.first_name,
        last_name=lead_data.last_name,
        email=lead_data.email,
        phone=lead_data.phone,
        notes=lead_data.notes,
        assigned_agent_id=lead_data.assigned_agent_id,
        tags=lead_data.tags or [],
        stage=LeadStage.NEW,
        classification=LeadClassification.COLD,
        source=LeadSource(lead_data.source.lower()) if lead_data.source else LeadSource.MANUAL
    )

    db.add(lead)
    db.commit()
    db.refresh(lead)

    return LeadResponse.from_lead(lead)


@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: UpdateLeadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> LeadResponse:
    """Update an existing lead."""

    # Check permission
    if not current_user.has_permission("edit_leads"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update leads"
        )

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Update fields
    if lead_data.first_name is not None:
        lead.first_name = lead_data.first_name
    if lead_data.last_name is not None:
        lead.last_name = lead_data.last_name
    if lead_data.email is not None:
        lead.email = lead_data.email
    if lead_data.phone is not None:
        lead.phone = lead_data.phone
    if lead_data.notes is not None:
        lead.notes = lead_data.notes
    if lead_data.assigned_agent_id is not None:
        lead.assigned_agent_id = lead_data.assigned_agent_id
    if lead_data.tags is not None:
        lead.tags = lead_data.tags

    # Update stage if provided
    if lead_data.stage is not None:
        try:
            new_stage = LeadStage(lead_data.stage.lower())
            lead.update_stage(new_stage)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {lead_data.stage}")

    # Update classification if provided
    if lead_data.classification is not None:
        try:
            lead.classification = LeadClassification(lead_data.classification.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid classification: {lead_data.classification}")

    db.commit()
    db.refresh(lead)

    return LeadResponse.from_lead(lead)


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Delete a lead."""

    # Check permission
    if not current_user.has_permission("delete_leads"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete leads"
        )

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    db.commit()

    return {"message": "Lead deleted successfully"}


@router.get("/leads/search")
async def search_leads(
    q: str = Query(..., description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[LeadResponse]:
    """Search leads by name, email, or phone."""

    # Check permission
    if not current_user.has_permission("view_leads"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to search leads"
        )

    search_term = f"%{q}%"
    leads = db.query(Lead).filter(
        (Lead.first_name.ilike(search_term)) |
        (Lead.last_name.ilike(search_term)) |
        (Lead.email.ilike(search_term)) |
        (Lead.phone.ilike(search_term))
    ).order_by(Lead.updated_at.desc()).limit(50).all()

    return [LeadResponse.from_lead(lead) for lead in leads]