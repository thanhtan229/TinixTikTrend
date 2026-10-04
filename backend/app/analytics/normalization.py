import math
from typing import Optional


def clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamps value to range [min_val, max_val]."""
    if math.isnan(value):
        return min_val
    return max(min_val, min(value, max_val))


def normalize_min_max(
    value: Optional[float],
    min_val: float,
    max_val: float,
    target_max: float = 100.0
) -> float:
    """
    Min-Max normalizes a value to [0, target_max].
    Handles zero division and missing values safely.
    """
    if value is None or math.isnan(value):
        return 0.0
    
    if max_val <= min_val:
        return target_max / 2.0 if value >= max_val else 0.0
        
    normalized = ((value - min_val) / (max_val - min_val)) * target_max
    return clamp(normalized, 0.0, target_max)


def log_scale_score(
    value: Optional[float],
    midpoint: float = 500.0,
    target_max: float = 100.0
) -> float:
    """
    Logarithmic scaling for heavy-tailed metrics like sales count or velocity.
    Formula: target_max * (log(1 + value) / log(1 + 10 * midpoint))
    """
    if value is None or value <= 0 or math.isnan(value):
        return 0.0
    
    # Scale smoothly such that value == midpoint yields ~60-70 points
    denom = math.log1p(midpoint * 10)
    score = (math.log1p(value) / denom) * target_max
    return clamp(score, 0.0, target_max)
