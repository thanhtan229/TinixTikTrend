from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import Category, Product, ProductSnapshot, CrawlRun, ProductVideoLink, WatchlistItem, SystemMetadata
from app.core.logging import logger, log_event
from app.models.quarantine import QuarantinedProduct
from datetime import datetime, timezone


DEFAULT_CATEGORIES = [
    {"name": "Thời trang & Phụ kiện", "slug": "fashion-accessories"},
    {"name": "Sức khỏe & Làm đẹp", "slug": "beauty-personal-care"},
    {"name": "Gia dụng & Đời sống", "slug": "home-living"},
    {"name": "Điện tử & Công nghệ", "slug": "electronics-gadgets"},
    {"name": "Mẹ & Bé", "slug": "mom-baby"},
    {"name": "Thực phẩm & Đồ uống", "slug": "food-beverages"},
]


def init_db(db: Session = None) -> None:
    """
    Initialize database schema (creates tables if they do not exist) and seed default categories.
    """
    # Create all tables
    Base.metadata.create_all(bind=db.get_bind() if db is not None else engine)
    
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
        
    try:
        # This additive table preserves every product and historical snapshot.
        contaminated = db.query(Product).filter(
            (Product.external_product_id.startswith("tt_item_")) |
            (Product.external_product_id.startswith("gen_"))
        ).all()
        for product in contaminated:
            if db.get(QuarantinedProduct, product.id) is None:
                db.add(QuarantinedProduct(product_id=product.id,
                    reason="Legacy unverified video/generated product; historical metrics cannot be trusted."))

        # Phase 3: One-time migration/backfill of the legacy tracked universe
        bootstrap_marker = db.get(SystemMetadata, "legacy_tracked_backfill_completed")
        if bootstrap_marker is None:
            legacy_tracked = db.query(Product).filter(
                Product.url.is_not(None),
                Product.id.not_in(select(QuarantinedProduct.product_id))
            ).all()
            for product in legacy_tracked:
                if db.query(WatchlistItem).filter_by(product_id=product.id).first() is None:
                    db.add(WatchlistItem(
                        product_id=product.id,
                        notes="Legacy tracked backfill"
                    ))
            db.add(SystemMetadata(
                key="legacy_tracked_backfill_completed",
                value="true"
            ))
            log_event("db_init", f"Backfilled {len(legacy_tracked)} legacy tracked products to Watchlist.")

        # Phase 4: Compatibility marker for portable database backups
        compat_marker = db.get(SystemMetadata, "portable_backup_compatibility_version")
        if compat_marker is None:
            db.add(SystemMetadata(
                key="portable_backup_compatibility_version",
                value="1"
            ))
            log_event("db_init", "Seeded portable_backup_compatibility_version = 1")

        for run in db.query(CrawlRun).filter(CrawlRun.status == "running").all():
            run.status = "partial" if run.snapshots_created else "failed"
            run.finished_at = datetime.now(timezone.utc)
            run.error_message = "Interrupted by application restart; committed snapshots were preserved."
        db.commit()
        # Seed categories if table is empty
        existing_categories = db.query(Category).count()
        if existing_categories == 0:
            for cat_data in DEFAULT_CATEGORIES:
                cat = Category(name=cat_data["name"], slug=cat_data["slug"], is_active=True)
                db.add(cat)
            db.commit()
            log_event("db_init", "Database tables created and default categories seeded.")
        else:
            log_event("db_init", "Database tables verified.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    init_db()
