from sqlalchemy import select, inspect, text
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import (
    Category,
    Product,
    ProductSnapshot,
    CrawlRun,
    ProductVideoLink,
    WatchlistItem,
    SystemMetadata,
    Collection,
    CollectionItem,
    SavedView,
    EconomicsScenario,
)
from app.core.logging import logger, log_event
from app.models.quarantine import QuarantinedProduct
from app.services.backup_service import BackupService
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
    bind = db.get_bind() if db is not None else engine
    Base.metadata.create_all(bind=bind)
    
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
        
    try:
        # create_all does not add constraints to pre-existing tables. This additive
        # unique index enforces one association per product/video pair after checking
        # that legacy data has no duplicates.
        duplicate_link = db.execute(text(
            "SELECT product_id, external_video_id FROM product_video_links "
            "GROUP BY product_id, external_video_id HAVING COUNT(*) > 1 LIMIT 1"
        )).first()
        if duplicate_link:
            raise RuntimeError(
                "Cannot enforce unique product/video links: duplicate legacy association "
                f"for product {duplicate_link[0]} and video {duplicate_link[1]}."
            )
        db.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_pvl_product_video "
            "ON product_video_links (product_id, external_video_id)"
        ))
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

        # Validate required schema derived dynamically from SQLAlchemy model metadata
        inspector = inspect(db.connection()) if db is not None else inspect(engine)
        existing_tables = set(inspector.get_table_names())
        required_schema = BackupService.get_required_schema()
        missing_tables = set(required_schema.keys()) - existing_tables
        if missing_tables:
            raise RuntimeError(f"Required schema validation failed: missing tables {sorted(list(missing_tables))}")
        for table_name, expected_cols in required_schema.items():
            actual_cols = {col["name"] for col in inspector.get_columns(table_name)}
            missing_cols = expected_cols - actual_cols
            if missing_cols:
                raise RuntimeError(
                    f"Required schema validation failed: table '{table_name}' missing columns {sorted(list(missing_cols))}"
                )

        # Phase 5: Compatibility marker for portable database backups (advances "1" -> "2")
        compat_marker = db.get(SystemMetadata, "portable_backup_compatibility_version")
        if compat_marker is None:
            db.add(SystemMetadata(
                key="portable_backup_compatibility_version",
                value=BackupService.COMPATIBILITY_VERSION,
            ))
            log_event("db_init", f"Seeded portable_backup_compatibility_version = {BackupService.COMPATIBILITY_VERSION}")
        elif compat_marker.value != BackupService.COMPATIBILITY_VERSION:
            old_val = compat_marker.value
            compat_marker.value = BackupService.COMPATIBILITY_VERSION
            compat_marker.updated_at = datetime.now(timezone.utc)
            log_event("db_init", f"Advanced portable_backup_compatibility_version from {old_val} to {BackupService.COMPATIBILITY_VERSION}")

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
