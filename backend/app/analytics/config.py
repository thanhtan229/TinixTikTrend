from pydantic import BaseModel, Field


class TrendScoreWeights(BaseModel):
    """
    Configurable weights for calculating Trend Score (0 to 100).
    Total should sum to 1.0 (or normalized automatically).
    """
    sales_velocity: float = Field(default=0.40, description="Weight for 24h sales velocity")
    sales_acceleration: float = Field(default=0.25, description="Weight for sales growth rate/acceleration")
    review_velocity: float = Field(default=0.15, description="Weight for 24h review velocity")
    freshness: float = Field(default=0.10, description="Weight for recency/freshness signal")
    rating: float = Field(default=0.10, description="Weight for product rating quality")


class AnalyticsConfig(BaseModel):
    weights: TrendScoreWeights = Field(default_factory=TrendScoreWeights)
    
    # Thresholds
    freshness_max_days: float = Field(default=14.0, description="Products older than this get 0 freshness score")
    min_rating_threshold: float = Field(default=3.5, description="Ratings below this scale down the rating score")


default_analytics_config = AnalyticsConfig()
