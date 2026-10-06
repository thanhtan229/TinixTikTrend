from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.collection_service import CollectionService

router = APIRouter(prefix="/collections", tags=["Collections"])


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class CollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AddCollectionItemRequest(BaseModel):
    product_id: int
    review_status: str = "new"
    notes: Optional[str] = Field(None, max_length=2000)


class UpdateCollectionItemRequest(BaseModel):
    review_status: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)


class ProductIdentity(BaseModel):
    id: int
    external_product_id: str
    title: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    shop_id: Optional[str] = None
    shop_name: Optional[str] = None
    category: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime


class CollectionMemberResponse(BaseModel):
    id: int
    collection_id: int
    product_id: int
    review_status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_watched: bool
    product: Optional[ProductIdentity] = None


class CollectionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    collection_id: int
    product_id: int
    review_status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProductCollectionMembershipResponse(BaseModel):
    collection_id: int
    collection_name: str
    collection_description: Optional[str] = None
    review_status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@router.get("", response_model=List[CollectionResponse])
def list_collections(db: Session = Depends(get_db)):
    service = CollectionService(db)
    return service.list_collections()


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)):
    service = CollectionService(db)
    return service.create_collection(name=payload.name, description=payload.description)


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(collection_id: int, db: Session = Depends(get_db)):
    service = CollectionService(db)
    return service.get_collection(collection_id)


@router.patch("/{collection_id}", response_model=CollectionResponse)
def update_collection(collection_id: int, payload: CollectionUpdate, db: Session = Depends(get_db)):
    service = CollectionService(db)
    return service.update_collection(collection_id, name=payload.name, description=payload.description)


@router.delete("/{collection_id}", status_code=status.HTTP_200_OK)
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    service = CollectionService(db)
    service.delete_collection(collection_id)
    return {"status": "ok", "message": f"Collection {collection_id} deleted"}


@router.get("/{collection_id}/items", response_model=List[CollectionMemberResponse])
def get_collection_members(collection_id: int, db: Session = Depends(get_db)):
    service = CollectionService(db)
    return service.get_collection_members(collection_id)


@router.post("/{collection_id}/items", response_model=CollectionItemResponse, status_code=status.HTTP_201_CREATED)
def add_product_to_collection(collection_id: int, payload: AddCollectionItemRequest, db: Session = Depends(get_db)):
    service = CollectionService(db)
    return service.add_product_to_collection(
        collection_id=collection_id,
        product_id=payload.product_id,
        review_status=payload.review_status,
        notes=payload.notes,
    )


@router.patch("/{collection_id}/items/{product_id}", response_model=CollectionItemResponse)
def update_collection_item(
    collection_id: int,
    product_id: int,
    payload: UpdateCollectionItemRequest,
    db: Session = Depends(get_db),
):
    service = CollectionService(db)
    return service.update_item(
        collection_id=collection_id,
        product_id=product_id,
        review_status=payload.review_status,
        notes=payload.notes,
    )


@router.delete("/{collection_id}/items/{product_id}", status_code=status.HTTP_200_OK)
def remove_product_from_collection(collection_id: int, product_id: int, db: Session = Depends(get_db)):
    service = CollectionService(db)
    service.remove_product_from_collection(collection_id=collection_id, product_id=product_id)
    return {"status": "ok", "message": f"Product {product_id} removed from collection {collection_id}"}


@router.get("/by-product/{product_id}", response_model=List[ProductCollectionMembershipResponse])
def get_collections_by_product(product_id: int, db: Session = Depends(get_db)):
    service = CollectionService(db)
    return service.get_collections_for_product(product_id)
