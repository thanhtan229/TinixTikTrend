import pytest
from fastapi.testclient import TestClient
from app.services import crawl_service
from app.services.crawl_service import CrawlService
from app.models import Product
from app.collectors.tiktok_shop.schemas import ExtractedProduct
from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_get_crawler_status(client: TestClient):
    response = client.get("/api/crawler/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data
    assert "region" in data
    assert "schedule" in data
    assert "latest_run" in data
    assert data["latest_run"] is not None


def test_list_crawler_runs(client: TestClient):
    response = client.get("/api/crawler/runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_duplicate_crawler_prevention(client: TestClient):
    # Simulate active crawler
    crawl_service._is_crawler_running = True
    try:
        response = client.post("/api/crawler/run")
        assert response.status_code == 409
        assert "already active" in response.json()["detail"]
    finally:
        crawl_service._is_crawler_running = False


@pytest.mark.asyncio
async def test_explicit_url_wins_over_tracked_url_for_same_product(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add(Product(external_product_id="123456", title="Known",
        url="https://shop.tiktok.com/view/product/123456", shop_name="Old shop"))
    db.commit()
    requested = "https://shop.tiktok.com/item/123456"
    visited = []

    class Collector:
        async def discover_products(self, query):
            raise AssertionError("Direct URL crawl should not run broad discovery")
        async def get_product(self, url):
            visited.append(url)
            return ExtractedProduct(external_product_id="123456", title="Updated",
                url=url, shop_name="Updated shop", sold_count=0)
        async def close(self):
            pass

    monkeypatch.setattr(crawl_service, "TikTokShopCollector", Collector)
    try:
        run = await CrawlService(db).execute_crawl(product_urls=[requested])
        assert visited == [requested]
        assert run.status == "completed" and run.products_updated == 1
        assert db.query(Product).count() == 1
        assert db.query(Product).one().url == requested
        assert db.query(Product).one().shop_name == "Updated shop"
    finally:
        CrawlService.release()
        db.close()
        engine.dispose()
