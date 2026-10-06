from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.saved_view_service import (
    SavedViewService,
    SavedViewCreate,
    SavedViewUpdate,
    SavedViewResponse,
)

router = APIRouter(prefix="/saved-views", tags=["Saved Views"])


@router.get("", response_model=List[SavedViewResponse])
def list_saved_views(scope: Optional[str] = Query(None), db: Session = Depends(get_db)):
    service = SavedViewService(db)
    return service.list_saved_views(scope=scope)


@router.post("", response_model=SavedViewResponse, status_code=status.HTTP_201_CREATED)
def create_saved_view(payload: SavedViewCreate, db: Session = Depends(get_db)):
    service = SavedViewService(db)
    return service.create_saved_view(payload)


@router.get("/{view_id}", response_model=SavedViewResponse)
def get_saved_view(view_id: int, db: Session = Depends(get_db)):
    service = SavedViewService(db)
    return service.get_saved_view(view_id)


@router.patch("/{view_id}", response_model=SavedViewResponse)
def update_saved_view(view_id: int, payload: SavedViewUpdate, db: Session = Depends(get_db)):
    service = SavedViewService(db)
    return service.update_saved_view(view_id, payload)


@router.delete("/{view_id}", status_code=status.HTTP_200_OK)
def delete_saved_view(view_id: int, db: Session = Depends(get_db)):
    service = SavedViewService(db)
    service.delete_saved_view(view_id)
    return {"status": "ok", "message": f"Saved view {view_id} deleted"}
