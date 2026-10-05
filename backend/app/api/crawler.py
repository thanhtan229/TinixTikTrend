import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from pydantic import BaseModel, Field, field_validator
from app.core.urls import validate_product_url
from app.collectors.tiktok_shop.discovery import CATEGORY_KEYWORDS
from app.analytics.deltas import ensure_utc
from app.core.exceptions import CrawlerActiveException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db, SessionLocal
from app.services.crawl_service import CrawlService
from app.models.crawl_run import CrawlRun
from app.models.quarantine import QuarantinedProduct
from app.core.config import settings
from app.collectors.tiktok_shop.session import session_status

router = APIRouter(prefix="/crawler", tags=["Crawler"])


class CrawlRequest(BaseModel):
    category_slugs: Optional[List[str]] = Field(default=None, max_length=6)
    product_urls: Optional[List[str]] = Field(default=None, max_length=100)
    keywords: Optional[List[str]] = Field(default=None, max_length=10)

    @field_validator("product_urls")
    @classmethod
    def product_links(cls, urls):
        if urls is None:
            return None
        validated = []
        errors = []
        for i, url in enumerate(urls):
            clean_url = url.strip() if isinstance(url, str) else url
            try:
                validated.append(validate_product_url(clean_url))
            except ValueError as e:
                errors.append(f"Dòng {i+1}: {e}")
        if errors:
            raise ValueError("; ".join(errors))
        return validated

    @field_validator("category_slugs")
    @classmethod
    def supported_categories(cls, slugs):
        if slugs and any(s not in CATEGORY_KEYWORDS for s in slugs):
            raise ValueError("Unsupported category slug.")
        return slugs

    @field_validator("keywords")
    @classmethod
    def search_terms(cls, keywords):
        if keywords and any(not k.strip() or len(k) > 200 for k in keywords):
            raise ValueError("Keywords must contain 1–200 characters.")
        return [k.strip() for k in keywords] if keywords is not None else None


async def run_crawler_task(
    category_slugs: Optional[List[str]] = None,
    product_urls: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
):
    db = None
    try:
        db = SessionLocal()
        service = CrawlService(db)
        await service.execute_crawl(
            source="manual",
            category_slugs=category_slugs,
            product_urls=product_urls,
            keywords=keywords,
            reserved=True,
        )
    finally:
        if db is not None:
            db.close()
        CrawlService.release()


@router.post("/run", response_model=Dict[str, Any])
async def trigger_crawl(
    background_tasks: BackgroundTasks,
    payload: Optional[CrawlRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Manually triggers a background crawler cycle.
    Rejects request if a crawl is already running.
    """
    service = CrawlService(db)
    try:
        service.reserve()
    except CrawlerActiveException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A crawler run is already active. Please wait for it to complete.",
        )

    cat_slugs = payload.category_slugs if payload else None
    prod_urls = payload.product_urls if payload else None
    kws = payload.keywords if payload else None

    background_tasks.add_task(
        run_crawler_task,
        category_slugs=cat_slugs,
        product_urls=prod_urls,
        keywords=kws,
    )
    return {
        "status": "triggered",
        "message": "Crawler run triggered in the background.",
        "schedule": settings.crawl_schedule,
    }


@router.get("/status", response_model=Dict[str, Any])
def get_crawler_status(db: Session = Depends(get_db)):
    """
    Returns current crawler status and information on the latest crawl run.
    """
    service = CrawlService(db)
    is_active = service.is_running()
    
    latest_run = db.query(CrawlRun).order_by(desc(CrawlRun.started_at)).first()
    
    latest_run_data = None
    if latest_run:
        latest_run_data = {
            "id": latest_run.id,
            "started_at": ensure_utc(latest_run.started_at),
            "finished_at": ensure_utc(latest_run.finished_at) if latest_run.finished_at else None,
            "status": latest_run.status,
            "source": latest_run.source,
            "products_found": latest_run.products_found,
            "products_created": latest_run.products_created,
            "products_updated": latest_run.products_updated,
            "snapshots_created": latest_run.snapshots_created,
            "error_message": latest_run.error_message,
        }

    return {
        "is_running": is_active,
        "region": settings.tiktok_region,
        "schedule": settings.crawl_schedule,
        "latest_run": latest_run_data,
        "quarantined_products": db.query(QuarantinedProduct).count(),
        "local_session_status": session_status(),
    }


@router.get("/runs", response_model=List[Dict[str, Any]])
def list_crawl_runs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    runs = db.query(CrawlRun).order_by(desc(CrawlRun.started_at)).limit(limit).all()
    return [
        {
            "id": r.id,
            "started_at": ensure_utc(r.started_at),
            "finished_at": ensure_utc(r.finished_at) if r.finished_at else None,
            "status": r.status,
            "source": r.source,
            "products_found": r.products_found,
            "products_created": r.products_created,
            "products_updated": r.products_updated,
            "snapshots_created": r.snapshots_created,
            "error_message": r.error_message,
        }
        for r in runs
    ]
