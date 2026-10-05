import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Generator, Optional
from fastapi import HTTPException
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.alert_event import AlertEvent
from app.services.trend_service import TrendService
from app.services.watchlist_service import WatchlistService


HISTORICAL_STREAM_BATCH_SIZE: int = 1000


def format_utc_z(dt: Optional[datetime]) -> str:
    """Formats a datetime object to standard ISO 8601 UTC Z format: YYYY-MM-DDTHH:MM:SSZ."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class ExportService:
    """
    Deterministic CSV export engine enforcing:
    1. Historical membership freeze (as_of_utc, lower_bound, max_id_at_start).
    2. Keyset pagination over short-lived database sessions (no transaction holds across download).
    3. UTF-8 BOM (utf-8-sig) for Microsoft Excel compatibility with Vietnamese diacritics.
    4. Exact display result-set parity for Trends and Watchlists (respecting filters/limit/offset).
    5. Internal historical batch size of 1000 rows.
    """

    @staticmethod
    def stream_product_history(
        product_id: int,
        time_range: str,
        batch_size: int = HISTORICAL_STREAM_BATCH_SIZE,
    ) -> Generator[str, None, None]:
        # Validate allowed range
        allowed_ranges = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}
        if time_range not in allowed_ranges:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Khoảng thời gian '{time_range}' không được hỗ trợ để xuất CSV. "
                    "Chỉ hỗ trợ: 24h, 7d, 30d. Khoảng 'Tất cả' chỉ hỗ trợ xem trực quan trên giao diện."
                ),
            )

        # Verify product exists
        with SessionLocal() as db:
            product = db.get(Product, product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

            # Freeze membership boundaries at request start
            as_of_utc = datetime.now(timezone.utc)
            lower_bound = as_of_utc - allowed_ranges[time_range]

            max_snapshot_id_at_start = db.scalar(
                select(func.max(ProductSnapshot.id)).where(
                    ProductSnapshot.product_id == product_id,
                    ProductSnapshot.captured_at >= lower_bound,
                    ProductSnapshot.captured_at <= as_of_utc,
                )
            ) or 0

        # Yield UTF-8 BOM and Header
        header_buf = io.StringIO()
        header_buf.write("\ufeff")  # UTF-8 BOM
        writer = csv.writer(header_buf)
        writer.writerow([
            "ID Snapshot",
            "Thoi gian ghi nhan (UTC)",
            "Gia (VND)",
            "Da ban",
            "Danh gia",
            "So luot danh gia",
        ])
        yield header_buf.getvalue()

        # Keyset pagination loop: (captured_at, id) ASC
        last_captured_at: Optional[datetime] = None
        last_id: Optional[int] = None

        while True:
            with SessionLocal() as db:
                query = (
                    select(ProductSnapshot)
                    .where(
                        ProductSnapshot.product_id == product_id,
                        ProductSnapshot.captured_at >= lower_bound,
                        ProductSnapshot.captured_at <= as_of_utc,
                        ProductSnapshot.id <= max_snapshot_id_at_start,
                    )
                )
                if last_captured_at is not None and last_id is not None:
                    query = query.where(
                        or_(
                            ProductSnapshot.captured_at > last_captured_at,
                            and_(
                                ProductSnapshot.captured_at == last_captured_at,
                                ProductSnapshot.id > last_id,
                            ),
                        )
                    )
                query = query.order_by(ProductSnapshot.captured_at.asc(), ProductSnapshot.id.asc()).limit(batch_size)
                snapshots = list(db.scalars(query).all())

            if not snapshots:
                break

            buf = io.StringIO()
            row_writer = csv.writer(buf)
            for s in snapshots:
                row_writer.writerow([
                    s.id,
                    format_utc_z(s.captured_at),
                    f"{s.price:.0f}" if s.price is not None else "",
                    s.sold_count if s.sold_count is not None else "",
                    f"{s.rating:.1f}" if s.rating is not None else "",
                    s.review_count if s.review_count is not None else "",
                ])

            last_captured_at = snapshots[-1].captured_at
            last_id = snapshots[-1].id

            yield buf.getvalue()

            if len(snapshots) < batch_size:
                break

    @staticmethod
    def export_trends_csv(
        category: Optional[str] = None,
        trend_state: Optional[str] = None,
        confidence: Optional[str] = None,
        evidence: Optional[str] = None,
        sort_by: str = "trend_score",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Generator[str, None, None]:
        with SessionLocal() as db:
            trend_service = TrendService(db)
            products = trend_service.get_trending_products(
                category=category,
                trend_state=trend_state or "eligible",
                confidence=confidence,
                evidence=evidence,
                sort_by=sort_by,
                order=sort_order,
                limit=(limit + offset) if offset else limit,
            )
            if offset:
                products = products[offset:offset + limit]


        buf = io.StringIO()
        buf.write("\ufeff")  # UTF-8 BOM
        writer = csv.writer(buf)
        writer.writerow([
            "ID San pham",
            "Ten san pham",
            "Ten Shop",
            "Nganh hang",
            "Diem xu huong",
            "Toc do ban 24h (don/ngay)",
            "Tang truong ban 24h",
            "Tang truong danh gia 24h",
            "Danh gia sao",
            "Do tin cay",
            "Trang thai",
            "Ly do xu huong",
            "Duong dan",
        ])

        for p in products:
            writer.writerow([
                p.product_id,
                p.title,
                p.shop_name or "",
                p.category or "",
                f"{p.trend_score:.1f}" if p.trend_score is not None else "",
                f"{p.deltas.sales_velocity_24h:.1f}" if p.deltas and p.deltas.sales_velocity_24h is not None else "",
                p.deltas.sold_delta_24h if p.deltas and p.deltas.sold_delta_24h is not None else "",
                p.deltas.review_delta_24h if p.deltas and p.deltas.review_delta_24h is not None else "",
                p.deltas.latest_rating if p.deltas and p.deltas.latest_rating is not None else "",
                p.evidence.confidence if p.evidence and p.evidence.confidence else "",
                p.evidence.ranking_state if p.evidence and p.evidence.ranking_state else "",
                "; ".join([r.formatted_text for r in p.reasons]) if p.reasons else "",
                p.url or "",
            ])

        yield buf.getvalue()

    @staticmethod
    def export_watchlist_csv(
        category: Optional[str] = None,
        trend_state: Optional[str] = None,
        confidence: Optional[str] = None,
        evidence: Optional[str] = None,
        sort_by: str = "trend_score",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Generator[str, None, None]:
        with SessionLocal() as db:
            wl_service = WatchlistService(db)
            watched_products, _ = wl_service.get_watched_products(
                category=category,
                trend_state=trend_state or "all",
                confidence=confidence,
                evidence=evidence,
                sort_by=sort_by,
                order=sort_order,
                skip=offset,
                limit=limit,
            )

        buf = io.StringIO()
        buf.write("\ufeff")  # UTF-8 BOM
        writer = csv.writer(buf)
        writer.writerow([
            "ID San pham",
            "Ten san pham",
            "Ten Shop",
            "Nganh hang",
            "Diem xu huong",
            "Toc do ban 24h (don/ngay)",
            "Tang truong ban 24h",
            "Tang truong danh gia 24h",
            "Danh gia sao",
            "Do tin cay",
            "Trang thai",
            "Ly do xu huong",
            "Duong dan",
        ])

        for p in watched_products:
            writer.writerow([
                p.product_id,
                p.title,
                p.shop_name or "",
                p.category or "",
                f"{p.trend_score:.1f}" if p.trend_score is not None else "",
                f"{p.deltas.sales_velocity_24h:.1f}" if p.deltas and p.deltas.sales_velocity_24h is not None else "",
                p.deltas.sold_delta_24h if p.deltas and p.deltas.sold_delta_24h is not None else "",
                p.deltas.review_delta_24h if p.deltas and p.deltas.review_delta_24h is not None else "",
                p.deltas.latest_rating if p.deltas and p.deltas.latest_rating is not None else "",
                p.evidence.confidence if p.evidence and p.evidence.confidence else "",
                p.evidence.ranking_state if p.evidence and p.evidence.ranking_state else "",
                "; ".join([r.formatted_text for r in p.reasons]) if p.reasons else "",
                p.url or "",
            ])

        yield buf.getvalue()

    @staticmethod
    def stream_alert_history(
        product_id: Optional[int] = None,
        is_read: Optional[bool] = None,
        batch_size: int = HISTORICAL_STREAM_BATCH_SIZE,
    ) -> Generator[str, None, None]:
        with SessionLocal() as db:
            max_event_id_at_start = db.scalar(select(func.max(AlertEvent.id))) or 0

        header_buf = io.StringIO()
        header_buf.write("\ufeff")  # UTF-8 BOM
        writer = csv.writer(header_buf)
        writer.writerow([
            "ID Canh bao",
            "Thoi gian tao (UTC)",
            "ID San pham",
            "Ten san pham",
            "Loai canh bao",
            "Nguong",
            "Gia tri thuc te",
            "Chieu huong",
            "Thong diep",
            "Trang thai doc",
        ])
        yield header_buf.getvalue()

        last_created_at: Optional[datetime] = None
        last_id: Optional[int] = None

        while True:
            with SessionLocal() as db:
                query = (
                    select(AlertEvent)
                    .options(joinedload(AlertEvent.product))
                    .where(AlertEvent.id <= max_event_id_at_start)
                )
                if product_id is not None:
                    query = query.where(AlertEvent.product_id == product_id)
                if is_read is not None:
                    query = query.where(AlertEvent.is_read == is_read)

                if last_created_at is not None and last_id is not None:
                    query = query.where(
                        or_(
                            AlertEvent.created_at < last_created_at,
                            and_(
                                AlertEvent.created_at == last_created_at,
                                AlertEvent.id < last_id,
                            ),
                        )
                    )
                query = query.order_by(AlertEvent.created_at.desc(), AlertEvent.id.desc()).limit(batch_size)
                events = list(db.scalars(query).all())

            if not events:
                break

            buf = io.StringIO()
            row_writer = csv.writer(buf)
            for e in events:
                row_writer.writerow([
                    e.id,
                    format_utc_z(e.created_at),
                    e.product_id,
                    e.product.title if e.product else "",
                    e.rule_type,
                    f"{e.threshold:.2f}" if e.threshold is not None else "",
                    f"{e.actual_value:.2f}" if e.actual_value is not None else "",
                    e.actual_direction or "",
                    e.message or "",
                    "Da doc" if e.is_read else "Chua doc",
                ])

            last_created_at = events[-1].created_at
            last_id = events[-1].id

            yield buf.getvalue()

            if len(events) < batch_size:
                break
