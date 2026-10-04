import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.init_db import init_db
from app.models import Product, ProductSnapshot, CrawlRun, QuarantinedProduct
from app.services import crawl_service as cs
from app.services.product_service import ProductService, get_analyzed_product
from app.services.trend_service import TrendService
from app.collectors.tiktok_shop.schemas import ExtractedProduct, DiscoveryQuery, DiscoveryResult
from app.collectors.tiktok_shop.discovery import ProductDiscovery
from app.collectors.tiktok_shop.parser import extract_product_from_html, parse_numeric_string
from app.collectors.tiktok_shop.client import TikTokHttpClient
from app.collectors.tiktok_shop.product import ProductCollector
from app.collectors.tiktok_shop.exceptions import BlockedError
from app.analytics.deltas import SnapshotData, calculate_product_deltas
from app.analytics.scoring import calculate_trend_score
from app.core.urls import validate_product_url, validate_public_destination
from app.api.crawler import CrawlRequest
from app.api import crawler
from fastapi.testclient import TestClient
from app.main import app
import httpx

URL = 'https://shop.tiktok.com/view/product/123456'


@pytest.mark.asyncio
async def test_saved_session_blocked_run_recovers_with_accurate_reason(isolated_db, monkeypatch):
    class Collector:
        async def get_product(self, url):
            raise BlockedError('Challenge')
        async def close(self):
            pass
    monkeypatch.setattr(cs, 'TikTokShopCollector', Collector)
    monkeypatch.setattr(cs, 'session_status', lambda: 'available')
    run = await cs.CrawlService(isolated_db).execute_crawl(product_urls=[URL])
    assert run.status == 'failed' and run.snapshots_created == 0
    assert 'Đã nạp phiên cục bộ' in run.error_message
    assert 'CONNECT_TIKTOK.bat' not in run.error_message
    assert not cs.CrawlService.is_running()


@pytest.mark.asyncio
async def test_security_check_stops_without_browser_or_fabricated_product():
    from types import SimpleNamespace
    http = SimpleNamespace(fetch_html=AsyncMock(return_value='<title>Security Check</title>'))
    browser = SimpleNamespace(get_new_page=AsyncMock())
    with pytest.raises(BlockedError):
        await ProductCollector(http, browser).get_product_by_url(URL)
    with pytest.raises(BlockedError):
        await ProductDiscovery(http, browser).discover(DiscoveryQuery())
    browser.get_new_page.assert_not_awaited()


@pytest.fixture
def isolated_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    yield db
    cs.CrawlService.release()
    db.close()
    engine.dispose()


def extracted(id='123456'):
    return ExtractedProduct(external_product_id=id, title='Verified Product',
        url=f'https://shop.tiktok.com/view/product/{id}', sold_count=100)


def test_blocked_html_and_video_never_become_products():
    assert extract_product_from_html('<title>Access Denied</title>', URL) is None
    assert extract_product_from_html('<title>Interesting video</title>', 'https://www.tiktok.com/@a/video/123') is None
    ld={'@type':'Product','name':'Real','productID':'123456','offers':{'price':'0','priceCurrency':'VND'}}
    p=extract_product_from_html('<script type="application/ld+json">'+json.dumps(ld)+'</script>',URL)
    assert p.price == 0 and p.sold_count is None and p.rating is None and p.commission_rate is None
    ld['productID']='98765'
    assert extract_product_from_html('<script type="application/ld+json">'+json.dumps(ld)+'</script>', URL) is None


@pytest.mark.parametrize('raw,count', [('12.500 sold',12500),('1,2K sold',1200),('12,500',12500),('2.5M',2500000),('0',0)])
def test_vietnamese_counts(raw,count):
    assert parse_numeric_string(raw)==count


@pytest.mark.parametrize('url', ['http://127.0.0.1:8000/api/health','https://evil.tiktok.com/product/123',
    'https://shop.tiktok.com.evil.test/product/123','https://user:pass@shop.tiktok.com/product/123',
    'https://shop.tiktok.com:444/product/123','https://www.tiktok.com/@a/video/123'])
def test_product_url_rejects_non_shop_destinations(url):
    with pytest.raises(ValueError): validate_product_url(url)
    with pytest.raises(ValueError): CrawlRequest(product_urls=[url])


@pytest.mark.asyncio
async def test_dns_private_destination_rejected(monkeypatch):
    loop=asyncio.get_running_loop()
    monkeypatch.setattr(loop,'getaddrinfo',AsyncMock(return_value=[(2,1,6,'',('127.0.0.1',443))]))
    with pytest.raises(ValueError): await validate_public_destination(URL)


@pytest.mark.asyncio
async def test_redirect_not_followed_into_private_network(monkeypatch):
    from app.collectors.tiktok_shop import client as module
    monkeypatch.setattr(module,'validate_public_destination',AsyncMock())
    calls=[]
    async def transport(request):
        calls.append(str(request.url))
        return httpx.Response(302,headers={'location':'http://127.0.0.1:8000/private'})
    http=TikTokHttpClient()
    http._client=httpx.AsyncClient(transport=httpx.MockTransport(transport),follow_redirects=False)
    monkeypatch.setattr(http,'_apply_rate_limit',AsyncMock())
    monkeypatch.setattr(module.settings,'max_retries',1)
    assert await http.fetch_html(URL) is None
    assert calls==[URL]
    await http.close()


def test_incomplete_gap_and_stale_windows():
    now=datetime.now(timezone.utc)
    short=[SnapshotData(captured_at=now-timedelta(hours=4),sold_count=100),SnapshotData(captured_at=now,sold_count=200)]
    d=calculate_product_deltas(short,now)
    assert d.sold_delta_6h is None and d.sold_delta_24h is None and d.sales_acceleration is None
    assert d.sales_velocity_24h==600 and d.velocity_is_estimated
    gap=[SnapshotData(captured_at=now-timedelta(days=30),sold_count=100),short[-1]]
    assert calculate_product_deltas(gap,now).sold_delta_7d is None
    assert calculate_product_deltas(gap,now).sales_velocity_24h is None
    stale=[SnapshotData(captured_at=now-timedelta(days=8),sold_count=100),SnapshotData(captured_at=now-timedelta(days=7),sold_count=1000)]
    d=calculate_product_deltas(stale,now)
    assert d.is_stale and d.sales_velocity_24h is None and d.sold_delta_24h is None
    assert calculate_trend_score(d,now-timedelta(days=10))==0


@pytest.mark.asyncio
async def test_keyword_refresh_dedupe_and_partial(isolated_db,monkeypatch):
    db=isolated_db
    p=Product(external_product_id='123456',title='Known',url=URL)
    db.add(p); db.commit(); db.add(ProductSnapshot(product_id=p.id,sold_count=90));db.commit()
    queries=[];fetched=[]
    class Collector:
        async def discover_products(self,q):
            queries.append(q)
            return DiscoveryResult(query=q,product_urls=[URL,URL+'?tracking=1'])
        async def get_product(self,url): fetched.append(url); return extracted()
        async def close(self): pass
    monkeypatch.setattr(cs,'TikTokShopCollector',Collector)
    run=await cs.CrawlService(db).execute_crawl(keywords=['son-moi'])
    assert queries[0].keyword=='son-moi' and queries[0].category_slug is None
    assert 'search?q=son-moi' in ProductDiscovery(None,None).build_discovery_url(queries[0])
    assert fetched==[URL] and run.snapshots_created==1 and run.products_updated==1
    assert len(db.get(Product,p.id).snapshots)==2
    class FailedDiscovery(Collector):
        async def discover_products(self,q): raise RuntimeError('blocked')
    monkeypatch.setattr(cs,'TikTokShopCollector',FailedDiscovery)
    run=await cs.CrawlService(db).execute_crawl(source='scheduled')
    assert run.status=='partial' and run.snapshots_created==1 and run.error_message


def test_food_category_uses_observed_vn_shop_breadcrumb_url():
    discovery=ProductDiscovery(None,None)
    assert discovery.build_discovery_url(DiscoveryQuery(category_slug='food-beverages')) == \
        'https://shop.tiktok.com/vn/c/food-beverages/700437'
    assert discovery.build_discovery_url(DiscoveryQuery()) == 'https://shop.tiktok.com/vn'


def test_trending_hides_products_without_measured_momentum(isolated_db):
    now=datetime.now(timezone.utc)
    unknown=Product(external_product_id='345678',title='Only cumulative totals',first_seen_at=now,last_seen_at=now)
    measured=Product(external_product_id='456789',title='Measured sales growth',first_seen_at=now-timedelta(days=2),last_seen_at=now)
    isolated_db.add_all([unknown,measured]);isolated_db.commit()
    isolated_db.add_all([
        ProductSnapshot(product_id=unknown.id,captured_at=now,sold_count=12808,review_count=730,rating=4.6),
        ProductSnapshot(product_id=measured.id,captured_at=now-timedelta(hours=24),sold_count=100,review_count=4,rating=4.6),
        ProductSnapshot(product_id=measured.id,captured_at=now,sold_count=200,review_count=8,rating=4.6),
    ]);isolated_db.commit()
    results=TrendService(isolated_db).get_trending_products()
    assert [p.external_product_id for p in results]==['456789']


@pytest.mark.asyncio
async def test_all_failed_and_failure_not_overwriting_metadata(isolated_db,monkeypatch):
    class Collector:
        async def get_product(self,url): raise TimeoutError('network lost')
        async def close(self): pass
    monkeypatch.setattr(cs,'TikTokShopCollector',Collector)
    run=await cs.CrawlService(isolated_db).execute_crawl(product_urls=[URL])
    assert run.status=='failed' and run.error_message and run.snapshots_created==0
    assert not cs.CrawlService.is_running()


@pytest.mark.asyncio
async def test_snapshot_failure_rolls_back_only_failed_product(isolated_db,monkeypatch):
    class Collector:
        async def get_product(self,url): return extracted(url.rsplit('/',1)[1])
        async def close(self): pass
    monkeypatch.setattr(cs,'TikTokShopCollector',Collector)
    service=cs.CrawlService(isolated_db)
    real=service.snapshot_service.create_snapshot_from_extracted
    def snapshot(**kwargs):
        if kwargs['extracted'].external_product_id=='123456': raise RuntimeError('failed after product flush')
        return real(**kwargs)
    monkeypatch.setattr(service.snapshot_service,'create_snapshot_from_extracted',snapshot)
    run=await service.execute_crawl(product_urls=[URL,'https://shop.tiktok.com/view/product/234567'])
    assert run.status=='partial' and run.products_created==1 and run.snapshots_created==1
    assert isolated_db.query(Product).count()==1 and isolated_db.query(ProductSnapshot).count()==1
    assert isolated_db.query(Product).one().external_product_id=='234567'


@pytest.mark.asyncio
async def test_real_sqlite_lock_releases_busy(tmp_path):
    import sqlite3
    path=tmp_path/'locked.db'
    engine=create_engine('sqlite:///'+str(path),connect_args={'timeout':0.01})
    Base.metadata.create_all(engine)
    db=sessionmaker(bind=engine)()
    blocker=sqlite3.connect(path);blocker.execute('BEGIN EXCLUSIVE')
    try:
        with pytest.raises(Exception): await cs.CrawlService(db).execute_crawl(product_urls=[URL])
        assert not cs.CrawlService.is_running()
    finally: blocker.rollback();blocker.close();db.close();engine.dispose()


def test_quarantine_and_startup_reconcile_preserve_history(isolated_db):
    db=isolated_db
    p=Product(external_product_id='tt_item_123',title='Old Video')
    db.add(p);db.commit();db.add(ProductSnapshot(product_id=p.id,sold_count=250,price=149000,rating=4.8))
    run=CrawlRun(status='running',source='test',snapshots_created=1)
    db.add(run);db.commit()
    init_db(db);init_db(db)
    assert db.query(Product).count()==1 and db.query(ProductSnapshot).count()==1
    assert db.query(QuarantinedProduct).count()==1
    assert ProductService(db).list_products()[1]==0
    assert ProductService(db).get_product_by_id(p.id) is None
    db.refresh(run);assert run.status=='partial' and run.finished_at and run.error_message


def test_api_timezone_and_security(client,monkeypatch):
    response=client.get('/api/products')
    product=response.json()['items'][0]
    assert product['first_seen_at'].endswith(('Z','+00:00'))
    detail=client.get('/api/products/'+str(product['product_id'])).json()
    assert detail['snapshots'][0]['captured_at'].endswith(('Z','+00:00'))
    assert client.post('/api/crawler/run',json={'product_urls':['http://127.0.0.1/']}).status_code==422
    assert client.post('/api/crawler/run',headers={'origin':'https://evil.example'},json={}).status_code==403
    assert client.get('/api/health',headers={'host':'evil.example'}).status_code==400
    assert not cs.CrawlService.is_running()


def test_request_reserves_before_background_starts(client,monkeypatch):
    async def noop(**kwargs): pass
    monkeypatch.setattr(crawler,'run_crawler_task',noop)
    try:
        assert client.post('/api/crawler/run',json={'product_urls':[URL]}).status_code==200
        assert client.post('/api/crawler/run',json={'product_urls':[URL]}).status_code==409
    finally: cs.CrawlService.release()
from app.analytics.best_sellers import rank_best_sellers
from app.analytics.rising_products import AnalyzedProduct
from app.analytics.deltas import DeltaMetrics


def test_recent_best_sellers_excludes_uncovered_or_stale():
    now=datetime.now(timezone.utc)
    unknown=AnalyzedProduct(product_id=1,external_product_id='1',title='Unknown',first_seen_at=now,last_seen_at=now,
        deltas=DeltaMetrics(latest_sold_count=100000),trend_score=0)
    covered=AnalyzedProduct(product_id=2,external_product_id='2',title='Covered',first_seen_at=now,last_seen_at=now,
        deltas=DeltaMetrics(latest_sold_count=100,sold_delta_24h=0),trend_score=0)
    assert rank_best_sellers([unknown,covered],rank_by='sold_delta_24h')==[covered]
    assert rank_best_sellers([unknown,covered],rank_by='total_sold')[0]==unknown
