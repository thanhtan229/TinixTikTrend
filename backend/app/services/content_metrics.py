from datetime import datetime
from typing import Iterable, Optional

from app.models.tiktok_video import VideoSnapshot

METRICS = ("view_count", "like_count", "comment_count", "share_count", "collect_count")


def calculate_content_metrics(snapshots: Iterable[VideoSnapshot]) -> dict:
    """Compute per-counter rates only from complete observations in the approved time window."""
    ordered = sorted(snapshots, key=lambda item: item.captured_at)
    latest = ordered[-1] if ordered else None
    result = {
        "velocities": {metric: None for metric in METRICS},
        "anomalies": {metric: False for metric in METRICS},
        "engagement_rate": None,
    }
    if latest is None:
        return result

    prior_candidates = [
        item for item in ordered[:-1]
        if 20 * 3600 <= (latest.captured_at - item.captured_at).total_seconds() <= 28 * 3600
    ]
    prior = min(prior_candidates, key=lambda item: abs((latest.captured_at - item.captured_at).total_seconds() - 86400)) if prior_candidates else None
    if prior is not None:
        elapsed_days = (latest.captured_at - prior.captured_at).total_seconds() / 86400
        for metric in METRICS:
            current_value, prior_value = getattr(latest, metric), getattr(prior, metric)
            if current_value is not None and prior_value is not None:
                delta = current_value - prior_value
                result["velocities"][metric] = delta / elapsed_days
                result["anomalies"][metric] = delta < 0

    engagement_fields = (latest.like_count, latest.comment_count, latest.share_count, latest.collect_count)
    if latest.view_count and latest.view_count > 0 and all(value is not None for value in engagement_fields):
        result["engagement_rate"] = sum(engagement_fields) / latest.view_count
    return result
