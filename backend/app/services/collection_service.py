from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.collection import Collection
from app.models.collection_item import CollectionItem, ALLOWED_REVIEW_STATUSES
from app.models.product import Product
from app.models.quarantine import QuarantinedProduct
from app.models.watchlist import WatchlistItem


class CollectionService:
    def __init__(self, db: Session):
        self.db = db

    def list_collections(self) -> List[Collection]:
        return self.db.query(Collection).order_by(Collection.created_at.desc()).all()

    def get_collection(self, collection_id: int) -> Collection:
        collection = self.db.get(Collection, collection_id)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Collection {collection_id} not found")
        return collection

    def create_collection(self, name: str, description: Optional[str] = None) -> Collection:
        clean_name = name.strip() if name else ""
        if not clean_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection name cannot be empty")
        
        clean_desc = description.strip() if description else None
        collection = Collection(
            name=clean_name,
            description=clean_desc,
        )
        self.db.add(collection)
        self.db.commit()
        self.db.refresh(collection)
        return collection

    def update_collection(self, collection_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Collection:
        collection = self.get_collection(collection_id)
        if name is not None:
            clean_name = name.strip()
            if not clean_name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection name cannot be empty")
            collection.name = clean_name
        if description is not None:
            collection.description = description.strip() if description else None
        collection.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(collection)
        return collection

    def delete_collection(self, collection_id: int) -> None:
        collection = self.get_collection(collection_id)
        # Explicitly delete dependent CollectionItems in same transaction to avoid orphan dependency issues
        self.db.query(CollectionItem).filter(CollectionItem.collection_id == collection_id).delete(synchronize_session=False)
        self.db.delete(collection)
        self.db.commit()

    def get_collection_members(self, collection_id: int) -> List[Dict[str, Any]]:
        """
        P5-AC-10: Collection member list uses <= 2 SQL queries with zero N+1 queries.
        Query 1: Ensure collection exists.
        Query 2: Eager join CollectionItem -> Product -> WatchlistItem.
        """
        self.get_collection(collection_id)

        items = (
            self.db.query(CollectionItem)
            .options(
                joinedload(CollectionItem.product).joinedload(Product.watchlist_item)
            )
            .filter(CollectionItem.collection_id == collection_id)
            .order_by(CollectionItem.created_at.asc())
            .all()
        )

        # Query 3: Batch load default economics for all products (P6-AC-33: <= 3 queries total, zero N+1)
        product_ids = [item.product_id for item in items if item.product_id]
        from app.services.economics_service import EconomicsService
        econ_service = EconomicsService(self.db)
        default_economics_map = econ_service.get_default_scenarios_for_products(product_ids)

        result = []
        for item in items:
            p = item.product
            is_watched = (p.watchlist_item is not None) if p else False
            result.append({
                "id": item.id,
                "collection_id": item.collection_id,
                "product_id": item.product_id,
                "review_status": item.review_status,
                "notes": item.notes,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "is_watched": is_watched,
                "product": {
                    "id": p.id,
                    "external_product_id": p.external_product_id,
                    "title": p.title,
                    "url": p.url,
                    "image_url": p.image_url,
                    "shop_id": p.shop_id,
                    "shop_name": p.shop_name,
                    "category": p.category,
                    "first_seen_at": p.first_seen_at,
                    "last_seen_at": p.last_seen_at,
                } if p else None,
                "default_economics": default_economics_map.get(item.product_id),
            })
        return result

    def add_product_to_collection(
        self,
        collection_id: int,
        product_id: int,
        review_status: str = "new",
        notes: Optional[str] = None,
    ) -> CollectionItem:
        # 1. Collection exists
        self.get_collection(collection_id)

        # 2. Status validation
        if review_status not in ALLOWED_REVIEW_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid review_status '{review_status}'. Allowed: {sorted(list(ALLOWED_REVIEW_STATUSES))}"
            )

        # 3. Product exists and not quarantined
        quarantined = self.db.query(QuarantinedProduct).filter(QuarantinedProduct.product_id == product_id).first()
        if quarantined:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {product_id} is quarantined and cannot be added to collections"
            )

        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )

        # 4. Check duplicate before insert
        existing = (
            self.db.query(CollectionItem)
            .filter_by(collection_id=collection_id, product_id=product_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product {product_id} is already a member of collection {collection_id}"
            )

        clean_notes = notes.strip() if notes else None
        item = CollectionItem(
            collection_id=collection_id,
            product_id=product_id,
            review_status=review_status,
            notes=clean_notes,
        )
        self.db.add(item)
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product {product_id} is already a member of collection {collection_id}"
            )

    def remove_product_from_collection(self, collection_id: int, product_id: int) -> None:
        self.get_collection(collection_id)
        item = (
            self.db.query(CollectionItem)
            .filter_by(collection_id=collection_id, product_id=product_id)
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} is not in collection {collection_id}"
            )
        self.db.delete(item)
        self.db.commit()

    def update_item(
        self,
        collection_id: int,
        product_id: int,
        review_status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> CollectionItem:
        self.get_collection(collection_id)
        item = (
            self.db.query(CollectionItem)
            .filter_by(collection_id=collection_id, product_id=product_id)
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} is not in collection {collection_id}"
            )

        if review_status is not None:
            if review_status not in ALLOWED_REVIEW_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid review_status '{review_status}'. Allowed: {sorted(list(ALLOWED_REVIEW_STATUSES))}"
                )
            item.review_status = review_status

        if notes is not None:
            item.notes = notes.strip() if notes.strip() else None

        item.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_collections_for_product(self, product_id: int) -> List[Dict[str, Any]]:
        # Reverse lookup using indexed collection_items(product_id)
        product = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.id.not_in(select(QuarantinedProduct.product_id)))
            .first()
        )
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found")

        items = (
            self.db.query(CollectionItem)
            .options(joinedload(CollectionItem.collection))
            .filter(CollectionItem.product_id == product_id)
            .all()
        )
        return [
            {
                "collection_id": it.collection.id,
                "collection_name": it.collection.name,
                "collection_description": it.collection.description,
                "review_status": it.review_status,
                "notes": it.notes,
                "created_at": it.created_at,
                "updated_at": it.updated_at,
            }
            for it in items if it.collection is not None
        ]
