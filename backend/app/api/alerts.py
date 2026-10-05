from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict

from app.db.session import get_db
from app.services.alert_service import AlertService
from app.services.export_service import ExportService
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.analytics.deltas import ensure_utc

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AlertRuleCreate(BaseModel):
    product_id: int
    rule_type: str = Field(..., description="sales_velocity_above, trend_score_above, or price_change_pct")
    threshold: float = Field(..., gt=0, description="Finite positive threshold")
    direction: Optional[str] = Field(None, description="up, down, or either for price rules; null for others")
    cooldown_minutes: int = Field(0, ge=0, description="Cooldown in minutes (default: 0)")


class AlertRuleUpdate(BaseModel):
    threshold: Optional[float] = Field(None, gt=0)
    direction: Optional[str] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0)
    is_enabled: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    rule_type: str
    threshold: float
    direction: Optional[str] = None
    cooldown_minutes: int
    is_enabled: bool
    last_evaluated_snapshot_id: Optional[int] = None
    last_condition_met: bool
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AlertEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: int
    product_id: int
    triggering_snapshot_id: int
    rule_type: str
    threshold: float
    actual_value: float
    actual_direction: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime
    product_title: Optional[str] = None
    product_image_url: Optional[str] = None


class AlertEventsEnvelope(BaseModel):
    items: List[AlertEventResponse]
    total: int
    skip: int
    limit: int


class UnreadCountResponse(BaseModel):
    unread_count: int


# Rules Endpoints
@router.get("/rules", response_model=List[AlertRuleResponse])
def list_rules(product_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    service = AlertService(db)
    if product_id is not None:
        rules = service.get_rules_for_product(product_id)
    else:
        rules = db.query(AlertRule).order_by(AlertRule.id.desc()).all()
    return rules


@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(payload: AlertRuleCreate, db: Session = Depends(get_db)):
    service = AlertService(db)
    try:
        rule = service.create_rule(
            product_id=payload.product_id,
            rule_type=payload.rule_type,
            threshold=payload.threshold,
            direction=payload.direction,
            cooldown_minutes=payload.cooldown_minutes,
        )
        return rule
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(AlertRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AlertRule {rule_id} not found.")
    return rule


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
def update_rule(rule_id: int, payload: AlertRuleUpdate, db: Session = Depends(get_db)):
    service = AlertService(db)
    try:
        rule = service.update_rule(
            rule_id=rule_id,
            threshold=payload.threshold,
            direction=payload.direction,
            cooldown_minutes=payload.cooldown_minutes,
            is_enabled=payload.is_enabled,
        )
        return rule
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    service = AlertService(db)
    deleted = service.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AlertRule {rule_id} not found.")
    return {"status": "ok", "deleted": True, "rule_id": rule_id}


# Events Endpoints
@router.get("/events", response_model=AlertEventsEnvelope)
def list_events(
    product_id: Optional[int] = Query(None),
    is_read: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(AlertEvent).options(joinedload(AlertEvent.product))
    if product_id is not None:
        q = q.filter(AlertEvent.product_id == product_id)
    if is_read is not None:
        q = q.filter(AlertEvent.is_read == is_read)

    total = q.count()
    events = q.order_by(AlertEvent.created_at.desc(), AlertEvent.id.desc()).offset(skip).limit(limit).all()

    items = [
        AlertEventResponse(
            id=ev.id,
            rule_id=ev.rule_id,
            product_id=ev.product_id,
            triggering_snapshot_id=ev.triggering_snapshot_id,
            rule_type=ev.rule_type,
            threshold=ev.threshold,
            actual_value=ev.actual_value,
            actual_direction=ev.actual_direction,
            message=ev.message,
            is_read=ev.is_read,
            created_at=ensure_utc(ev.created_at),
            product_title=ev.product.title if ev.product else None,
            product_image_url=ev.product.image_url if ev.product else None,
        )
        for ev in events
    ]

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/events/export")
def export_alert_events_csv(
    product_id: Optional[int] = Query(None, description="Lọc theo ID sản phẩm"),
    is_read: Optional[bool] = Query(None, description="Lọc theo trạng thái đọc"),
):
    """
    Export alert event history as a UTF-8 BOM CSV using keyset streaming.
    """
    generator = ExportService.stream_alert_history(
        product_id=product_id,
        is_read=is_read,
    )
    filename = "alerts_export.csv"
    return StreamingResponse(
        generator,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(db: Session = Depends(get_db)):
    service = AlertService(db)
    return {"unread_count": service.get_unread_count()}


@router.patch("/events/{event_id}/read")
def mark_event_read(event_id: int, db: Session = Depends(get_db)):
    service = AlertService(db)
    success = service.mark_event_read(event_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AlertEvent {event_id} not found.")
    return {"status": "ok", "event_id": event_id, "is_read": True}


@router.post("/events/mark-all-read")
def mark_all_events_read(product_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    service = AlertService(db)
    marked_count = service.mark_all_events_read(product_id=product_id)
    return {"status": "ok", "marked_read_count": marked_count}
