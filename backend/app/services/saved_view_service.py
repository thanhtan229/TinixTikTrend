from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Literal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.models.saved_view import SavedView, ALLOWED_SCOPES


class TrendsSavedViewPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Optional[str]
    trend_state: Literal["all", "eligible", "stale", "insufficient_signal"]
    measured_only: bool
    confidence: Optional[Literal["low", "medium", "high"]]
    sort_by: Literal["trend_score", "sales_velocity", "sales_delta", "review_delta", "freshness"]
    sort_direction: Literal["asc", "desc"]
    limit: int = Field(..., ge=1, le=100)
    search: str
    min_score: Optional[float]

    @field_validator("min_score")
    @classmethod
    def validate_min_score(cls, v):
        if v is not None and v < 0:
            raise ValueError("min_score must be >= 0 or None")
        return v


class WatchlistSavedViewPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Optional[str]
    trend_state: Literal["all", "eligible", "stale", "insufficient_signal"]
    measured_only: bool
    confidence: Optional[Literal["low", "medium", "high"]]
    sort_by: Literal["trend_score", "sales_velocity", "sales_delta", "review_delta", "freshness"]
    sort_direction: Literal["asc", "desc"]
    limit: int = Field(..., ge=1, le=100)


class SavedViewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scope: Literal["trends", "watchlist"]
    payload_version: int = 1
    payload: Dict[str, Any]

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        clean = v.strip() if v else ""
        if not clean:
            raise ValueError("Name cannot be empty")
        return clean

    @field_validator("payload_version")
    @classmethod
    def validate_version(cls, v):
        if v != 1:
            raise ValueError("Only payload_version = 1 is supported")
        return v

    @model_validator(mode="after")
    def validate_scope_payload(self):
        if self.scope == "trends":
            TrendsSavedViewPayload(**self.payload)
        elif self.scope == "watchlist":
            WatchlistSavedViewPayload(**self.payload)
        return self


class SavedViewUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    scope: Optional[str] = None
    payload_version: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            clean = v.strip()
            if not clean:
                raise ValueError("Name cannot be empty")
            return clean
        return v

    @field_validator("payload_version")
    @classmethod
    def validate_version(cls, v):
        if v is not None and v != 1:
            raise ValueError("Only payload_version = 1 is supported")
        return v


class SavedViewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    scope: str
    payload_version: int
    payload: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SavedViewService:
    def __init__(self, db: Session):
        self.db = db

    def list_saved_views(self, scope: Optional[str] = None) -> List[SavedView]:
        q = self.db.query(SavedView)
        if scope:
            if scope not in ALLOWED_SCOPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid scope '{scope}'. Allowed: {sorted(list(ALLOWED_SCOPES))}"
                )
            q = q.filter(SavedView.scope == scope)
        return q.order_by(SavedView.created_at.desc()).all()

    def get_saved_view(self, view_id: int) -> SavedView:
        view = self.db.get(SavedView, view_id)
        if not view:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Saved view {view_id} not found")
        return view

    def create_saved_view(self, data: SavedViewCreate) -> SavedView:
        # Pydantic validation has already validated name, scope, version, and payload
        view = SavedView(
            name=data.name,
            scope=data.scope,
            payload_version=data.payload_version,
            payload=data.payload,
        )
        self.db.add(view)
        self.db.commit()
        self.db.refresh(view)
        return view

    def update_saved_view(self, view_id: int, data: SavedViewUpdate) -> SavedView:
        view = self.get_saved_view(view_id)

        # Scope is strictly immutable
        if data.scope is not None and data.scope != view.scope:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Saved view scope is immutable (cannot change from '{view.scope}' to '{data.scope}')"
            )

        if data.payload_version is not None and data.payload_version != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only payload_version = 1 is supported"
            )

        if data.payload is not None:
            # Validate payload according to existing immutable scope
            try:
                if view.scope == "trends":
                    TrendsSavedViewPayload(**data.payload)
                elif view.scope == "watchlist":
                    WatchlistSavedViewPayload(**data.payload)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
            view.payload = data.payload

        if data.name is not None:
            view.name = data.name

        view.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(view)
        return view

    def delete_saved_view(self, view_id: int) -> None:
        view = self.get_saved_view(view_id)
        self.db.delete(view)
        self.db.commit()
