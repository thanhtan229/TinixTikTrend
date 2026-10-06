from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.compare_service import (
    CompareService,
    CompareRequest,
    CompareResponse,
)

router = APIRouter(prefix="/compare", tags=["Compare"])


@router.post("", response_model=CompareResponse)
def compare_products(payload: CompareRequest, db: Session = Depends(get_db)):
    service = CompareService(db)
    return service.compare_products(
        product_ids=payload.product_ids,
        collection_id=payload.collection_id,
    )
