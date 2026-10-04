from datetime import datetime, timezone, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.crawl_run import CrawlRun
from app.models.category import Category


def seed_sample_data(db: Session) -> None:
    """
    Seeds controlled development fixtures strictly for testing analytics and API layers.
    NOTE: These are simulated records and MUST NOT be treated as live TikTok Shop data.
    """
    # Check if already seeded
    if db.query(Product).count() > 0:
        return

    now = datetime.now(timezone.utc)
    t_24h = now - timedelta(hours=24)
    t_12h = now - timedelta(hours=12)
    t_6h = now - timedelta(hours=6)

    # 1. Create a simulated CrawlRun
    run = CrawlRun(
        started_at=t_24h,
        finished_at=now,
        source="fixture",
        status="completed",
        products_found=5,
        products_created=5,
        products_updated=0,
        snapshots_created=15,
    )
    db.add(run)
    db.flush()

    # Product 1: Rapidly Rising Product (Strong sales velocity & acceleration)
    p1 = Product(
        platform="tiktok_shop",
        external_product_id="vn_prod_001_rising",
        title="Son Kem Lì Mịn Môi Kháng Nước Velvet Lip Tint 5g",
        url="https://shop.tiktok.com/view/product/17293849102",
        image_url="https://p16-va.lemon8cdn.com/tos-alisg-v-a3e472/oIDefA9.jpg",
        shop_id="shop_beauty_vn_99",
        shop_name="Cosmetics Official Store VN",
        category="Sức khỏe & Làm đẹp",
        first_seen_at=t_24h,
        last_seen_at=now,
    )
    db.add(p1)
    db.flush()

    # Snapshots for P1: 500 (24h ago) -> 800 (12h ago) -> 1,400 (6h ago) -> 2,300 (now)
    db.add_all([
        ProductSnapshot(product_id=p1.id, crawl_run_id=run.id, captured_at=t_24h, price=149000, original_price=220000, sold_count=500, review_count=45, rating=4.8, commission_rate=15.0),
        ProductSnapshot(product_id=p1.id, crawl_run_id=run.id, captured_at=t_12h, price=149000, original_price=220000, sold_count=800, review_count=65, rating=4.85, commission_rate=15.0),
        ProductSnapshot(product_id=p1.id, crawl_run_id=run.id, captured_at=t_6h, price=149000, original_price=220000, sold_count=1400, review_count=110, rating=4.9, commission_rate=15.0),
        ProductSnapshot(product_id=p1.id, crawl_run_id=run.id, captured_at=now, price=149000, original_price=220000, sold_count=2300, review_count=195, rating=4.92, commission_rate=15.0),
    ])

    # Product 2: High Lifetime Best Seller (Slow current velocity)
    p2 = Product(
        platform="tiktok_shop",
        external_product_id="vn_prod_002_bestseller",
        title="Áo Thun Nữ Cổ Tròn Cotton 100% Co Giãn Unisex",
        url="https://shop.tiktok.com/view/product/17293849103",
        image_url="https://p16-va.lemon8cdn.com/tos-alisg-v-a3e472/oIDefA9_tshirt.jpg",
        shop_id="shop_fashion_vn_01",
        shop_name="GenZ Fashion House",
        category="Thời trang & Phụ kiện",
        first_seen_at=now - timedelta(days=30),
        last_seen_at=now,
    )
    db.add(p2)
    db.flush()

    # Snapshots for P2: 60,000 (24h ago) -> 60,040 (12h ago) -> 60,070 (6h ago) -> 60,110 (now)
    db.add_all([
        ProductSnapshot(product_id=p2.id, crawl_run_id=run.id, captured_at=t_24h, price=89000, original_price=150000, sold_count=60000, review_count=8200, rating=4.7, commission_rate=10.0),
        ProductSnapshot(product_id=p2.id, crawl_run_id=run.id, captured_at=t_12h, price=89000, original_price=150000, sold_count=60040, review_count=8210, rating=4.7, commission_rate=10.0),
        ProductSnapshot(product_id=p2.id, crawl_run_id=run.id, captured_at=t_6h, price=89000, original_price=150000, sold_count=60070, review_count=8215, rating=4.7, commission_rate=10.0),
        ProductSnapshot(product_id=p2.id, crawl_run_id=run.id, captured_at=now, price=89000, original_price=150000, sold_count=60110, review_count=8222, rating=4.7, commission_rate=10.0),
    ])

    # Product 3: Brand New Detected Product (Freshness signal)
    p3 = Product(
        platform="tiktok_shop",
        external_product_id="vn_prod_003_fresh",
        title="Quạt Cầm Tay Mini Tích Điện 5 Cấp Độ Gió Siêu Mát Màn Hình LED",
        url="https://shop.tiktok.com/view/product/17293849104",
        image_url="https://p16-va.lemon8cdn.com/tos-alisg-v-a3e472/oIDefA9_fan.jpg",
        shop_id="shop_gadgets_vn_55",
        shop_name="Smart Tech Vietnam",
        category="Điện tử & Công nghệ",
        first_seen_at=now - timedelta(hours=3),
        last_seen_at=now,
    )
    db.add(p3)
    db.flush()

    db.add_all([
        ProductSnapshot(product_id=p3.id, crawl_run_id=run.id, captured_at=now - timedelta(hours=3), price=129000, original_price=250000, sold_count=120, review_count=12, rating=5.0, commission_rate=18.0),
        ProductSnapshot(product_id=p3.id, crawl_run_id=run.id, captured_at=now, price=129000, original_price=250000, sold_count=350, review_count=38, rating=4.95, commission_rate=18.0),
    ])

    # Product 4: Product with missing optional fields (testing null-resilience)
    p4 = Product(
        platform="tiktok_shop",
        external_product_id="vn_prod_004_partial",
        title="Bình Nước Giữ Nhiệt Inox 316 Cao Cấp 1000ml",
        url="https://shop.tiktok.com/view/product/17293849105",
        image_url=None,
        shop_id="shop_home_88",
        shop_name="Living Life Store",
        category="Gia dụng & Đời sống",
        first_seen_at=t_12h,
        last_seen_at=now,
    )
    db.add(p4)
    db.flush()

    db.add_all([
        ProductSnapshot(product_id=p4.id, crawl_run_id=run.id, captured_at=t_12h, price=199000, original_price=None, sold_count=1500, review_count=None, rating=None, commission_rate=None, is_partial=True),
        ProductSnapshot(product_id=p4.id, crawl_run_id=run.id, captured_at=now, price=199000, original_price=None, sold_count=1650, review_count=None, rating=None, commission_rate=None, is_partial=True),
    ])

    db.commit()
