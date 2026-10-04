import pytest
from fastapi.testclient import TestClient


def test_api_list_products(client: TestClient):
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 4
    assert len(data["items"]) >= 4


def test_api_get_product_detail(client: TestClient):
    list_res = client.get("/api/products")
    first_id = list_res.json()["items"][0]["product_id"]

    response = client.get(f"/api/products/{first_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_id
    assert "analysis" in data
    assert "snapshots" in data
    assert len(data["snapshots"]) >= 1


def test_api_get_product_404(client: TestClient):
    response = client.get("/api/products/999999")
    assert response.status_code == 404


def test_api_trends_all(client: TestClient):
    response = client.get("/api/trends")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    scores = [p["trend_score"] for p in data]
    assert scores == sorted(scores, reverse=True)


def test_api_trends_rising(client: TestClient):
    response = client.get("/api/trends/rising")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["external_product_id"] == "vn_prod_001_rising"


def test_api_trends_new(client: TestClient):
    response = client.get("/api/trends/new?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    ids = [p["external_product_id"] for p in data]
    assert "vn_prod_003_fresh" in ids


def test_api_trends_best_sellers(client: TestClient):
    response = client.get("/api/trends/best-sellers?rank_by=total_sold")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["external_product_id"] == "vn_prod_002_bestseller"


def test_api_dashboard_summary(client: TestClient):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "trending" in data
    assert "rising" in data
    assert "new_products" in data
    assert "best_sellers" in data
    assert data["stats"]["total_products"] >= 4
