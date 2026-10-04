import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.crawl_run import CrawlRun
from app.models.quarantine import QuarantinedProduct
from app.collectors.tiktok_shop import TikTokShopCollector, DiscoveryQuery, ExtractedProduct
from app.collectors.tiktok_shop.exceptions import BlockedError
from app.collectors.tiktok_shop.session import SessionStateError, session_status
from app.services.snapshot_service import SnapshotService
from app.core.exceptions import CrawlerActiveException
from app.core.config import settings
from app.core.urls import validate_product_url, product_id_from_url
from app.core.logging import logger, log_event

_crawler_lock = asyncio.Lock()
_is_crawler_running = False
def blocked_message() -> str:
    prefix = 'TikTok trả trang Security Check thay cho dữ liệu. '
    if session_status() == 'available':
        return prefix + 'Đã nạp phiên cục bộ nhưng trang sản phẩm vẫn bị chặn. Hãy thử URL sản phẩm đang mở được trong phiên đăng nhập hoặc thử lại sau. Chưa lưu số liệu từ trang này.'
    return prefix + 'Chạy CONNECT_TIKTOK.bat để tự đăng nhập và lưu phiên cục bộ, rồi thử lại. Chưa lưu số liệu từ trang này.'


class CrawlService:
    def __init__(self, db: Session):
        self.db = db
        self.snapshot_service = SnapshotService(db)

    @staticmethod
    def is_running() -> bool:
        return _is_crawler_running

    @staticmethod
    def reserve() -> None:
        global _is_crawler_running
        if _is_crawler_running:
            raise CrawlerActiveException('A crawler run is already in progress.')
        _is_crawler_running = True

    @staticmethod
    def release() -> None:
        global _is_crawler_running
        _is_crawler_running = False

    def _upsert_product_and_snapshot(self, extracted: ExtractedProduct, crawl_run: CrawlRun) -> None:
        # Collector output must prove identity; never upsert title-only/video data.
        url = validate_product_url(extracted.url or '')
        if product_id_from_url(url) != extracted.external_product_id or not extracted.title.strip():
            raise ValueError('Unverified TikTok Shop product identity.')
        if extracted.is_partial:
            raise ValueError('The product page did not provide verified product data.')
        try:
            product = self.db.query(Product).filter_by(external_product_id=extracted.external_product_id).first()
            created = product is None
            if created:
                product = Product(platform=extracted.platform, external_product_id=extracted.external_product_id,
                    title=extracted.title, url=url, first_seen_at=extracted.captured_at,
                    last_seen_at=extracted.captured_at)
                self.db.add(product)
                self.db.flush()
            else:
                if self.db.get(QuarantinedProduct, product.id):
                    raise ValueError('Product is quarantined and requires provenance review.')
                product.title = extracted.title
                product.url = url
                product.last_seen_at = extracted.captured_at
            for field in ('image_url', 'shop_id', 'shop_name', 'category'):
                setattr(product, field, getattr(extracted, field))
            self.snapshot_service.create_snapshot_from_extracted(product_id=product.id,
                extracted=extracted, crawl_run_id=crawl_run.id)
            if created:
                crawl_run.products_created += 1
            else:
                crawl_run.products_updated += 1
            crawl_run.snapshots_created += 1
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    async def execute_crawl(self, source: str = 'manual', category_slugs: Optional[List[str]] = None,
                            product_urls: Optional[List[str]] = None, keywords: Optional[List[str]] = None,
                            reserved: bool = False) -> CrawlRun:
        if not reserved:
            self.reserve()
        collector = None
        run_id = None
        errors = []
        crawl_run = None
        try:
            async with _crawler_lock:
                crawl_run = CrawlRun(started_at=datetime.now(timezone.utc), source=source, status='running',
                    products_found=0, products_created=0, products_updated=0, snapshots_created=0)
                self.db.add(crawl_run)
                self.db.commit()
                self.db.refresh(crawl_run)
                run_id = crawl_run.id
                collector = TikTokShopCollector()
                # Oldest observed first: rotate a bounded set instead of starving older products.
                tracked = self.db.query(Product).filter(Product.url.is_not(None),
                    Product.id.not_in(select(QuarantinedProduct.product_id))).order_by(Product.last_seen_at).limit(
                    settings.tracked_products_per_run).all()
                candidates = list(product_urls or []) + [p.url for p in tracked]
                queries = [DiscoveryQuery(keyword=k, limit=10) for k in (keywords or [])]
                queries += [DiscoveryQuery(category_slug=c, limit=10) for c in (category_slugs or [])]
                if not queries and not product_urls:
                    queries = [DiscoveryQuery(limit=10)]
                direct = []
                for query in queries:
                    try:
                        found = await collector.discover_products(query)
                        candidates.extend(found.product_urls)
                        direct.extend(found.products)
                    except SessionStateError as exc:
                        errors.append(exc.message)
                    except BlockedError:
                        errors.append(blocked_message())
                    except Exception:
                        errors.append('Không tìm được link TikTok Shop đã xác minh. Dán URL đầy đủ của sản phẩm đang truy cập được hoặc thử lại sau.')
                urls = {}
                for candidate in candidates:
                    try:
                        clean = validate_product_url(candidate)
                        # Explicit URLs come first: do not replace a newly supplied
                        # accessible PDP with an older tracked URL for the same ID.
                        urls.setdefault(product_id_from_url(clean), clean)
                    except ValueError:
                        errors.append('Đã bỏ qua một URL sản phẩm không hợp lệ.')
                crawl_run.products_found = len(set(urls) | {p.external_product_id for p in direct})
                self.db.commit()
                processed = set()
                for product in direct:
                    if product.external_product_id in processed:
                        continue
                    try:
                        self._upsert_product_and_snapshot(product, crawl_run)
                        processed.add(product.external_product_id)
                    except Exception:
                        errors.append('Một sản phẩm tìm thấy chưa xác minh được hoặc chưa lưu được.')
                for external_id, url in urls.items():
                    if external_id in processed:
                        continue
                    try:
                        product = await collector.get_product(url)
                        if product is None:
                            raise ValueError('No verified product payload')
                        self._upsert_product_and_snapshot(product, crawl_run)
                        processed.add(external_id)
                    except SessionStateError as exc:
                        self.db.rollback()
                        errors.append(exc.message)
                    except BlockedError:
                        self.db.rollback()
                        errors.append(blocked_message())
                    except Exception:
                        self.db.rollback()
                        errors.append('Một trang sản phẩm không truy cập được, bị chặn, chưa hỗ trợ hoặc chưa lưu được.')
                crawl_run.status = ('partial' if crawl_run.snapshots_created else 'failed') if errors else 'completed'
                crawl_run.error_message = ' '.join(dict.fromkeys(errors))[:2000] if errors else None
                crawl_run.finished_at = datetime.now(timezone.utc)
                self.db.commit()
                return crawl_run
        except BaseException:
            self.db.rollback()
            if run_id is not None:
                try:
                    run = self.db.get(CrawlRun, run_id)
                    run.status = 'partial' if run.snapshots_created else 'failed'
                    run.finished_at = datetime.now(timezone.utc)
                    run.error_message = 'Lần quét bị gián đoạn hoặc database chưa ghi được; các snapshots đã lưu vẫn được giữ.'
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                    logger.error('Could not persist crawl failure; startup will reconcile the interrupted run.')
            raise
        finally:
            try:
                if collector:
                    await collector.close()
            finally:
                self.release()
