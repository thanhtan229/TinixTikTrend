import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.crawl_run import CrawlRun
from app.models.category import Category
from app.models.product_video_link import ProductVideoLink
from app.fixtures.sample_data import seed_sample_data


@pytest.fixture
def db_session():
    # Use in-memory SQLite database for fast isolated testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_product_and_snapshot_creation(db_session):
    now = datetime.now(timezone.utc)
    
    product = Product(
        platform="tiktok_shop",
        external_product_id="test_prod_1001",
        title="Áo Polo Nam Cao Cấp",
        shop_name="Men Fashion Store",
        category="Thời trang & Phụ kiện",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    assert product.id is not None
    assert product.external_product_id == "test_prod_1001"

    # Add snapshot
    snap1 = ProductSnapshot(
        product_id=product.id,
        captured_at=now - timedelta(hours=1),
        price=180000.0,
        sold_count=50,
        review_count=5,
        rating=4.9,
    )
    snap2 = ProductSnapshot(
        product_id=product.id,
        captured_at=now,
        price=180000.0,
        sold_count=120,
        review_count=12,
        rating=4.95,
    )
    db_session.add_all([snap1, snap2])
    db_session.commit()

    db_session.refresh(product)
    assert len(product.snapshots) == 2
    assert product.snapshots[0].sold_count == 50
    assert product.snapshots[1].sold_count == 120


def test_cascade_delete_product(db_session):
    now = datetime.now(timezone.utc)
    product = Product(
        platform="tiktok_shop",
        external_product_id="test_prod_cascade",
        title="Test Cascade Delete",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    snap = ProductSnapshot(
        product_id=product.id,
        captured_at=now,
        sold_count=100,
    )
    db_session.add(snap)
    db_session.commit()

    # Delete product
    db_session.delete(product)
    db_session.commit()

    # Verify snapshots are also deleted
    snapshots = db_session.query(ProductSnapshot).filter_by(product_id=product.id).all()
    assert len(snapshots) == 0


def test_product_video_link(db_session):
    now = datetime.now(timezone.utc)
    product = Product(
        platform="tiktok_shop",
        external_product_id="test_prod_video",
        title="Test Video Linking",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(product)
    db_session.commit()

    link = ProductVideoLink(
        product_id=product.id,
        external_video_id="video_718293819203",
        creator_id="creator_vn_01",
        source="product_page",
        confidence=0.95,
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(link)
    db_session.commit()

    db_session.refresh(product)
    assert len(product.video_links) == 1
    assert product.video_links[0].external_video_id == "video_718293819203"
    assert product.video_links[0].confidence == 0.95


def test_seed_sample_data(db_session):
    seed_sample_data(db_session)
    products = db_session.query(Product).all()
    assert len(products) >= 4
    
    # Check rising product snapshots
    rising_prod = db_session.query(Product).filter_by(external_product_id="vn_prod_001_rising").first()
    assert rising_prod is not None
    assert len(rising_prod.snapshots) == 4
