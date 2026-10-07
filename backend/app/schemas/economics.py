from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

JS_MAX_SAFE_INTEGER: int = 9_007_199_254_740_991  # 2^53 - 1


def validate_safe_integer_monetary_outputs(
    base_vnd: Optional[int] = None,
    rate_bps: Optional[int] = None,
    sample_cost_vnd: Optional[int] = None,
    content_cost_vnd: Optional[int] = None,
    promotion_cost_vnd: Optional[int] = None,
    variable_cost_per_attributed_order_vnd: Optional[int] = None,
    expected_attributed_orders: Optional[int] = None,
) -> None:
    """
    Validates that no mathematically derived whole integer monetary output
    exceeds Number.MAX_SAFE_INTEGER (9,007,199,254,740,991).
    Uses exact integer arithmetic.
    """
    # 1. Commission per attributable order
    if base_vnd is not None and rate_bps is not None:
        comm_per_order = (2 * base_vnd * rate_bps + 10_000) // 20_000
        if comm_per_order > JS_MAX_SAFE_INTEGER:
            raise ValueError(
                f"Hoa hồng ước tính mỗi đơn ({comm_per_order}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
            )

    # 2. Fixed campaign cost sum
    fixed_sum = 0
    for cost in [sample_cost_vnd, content_cost_vnd, promotion_cost_vnd]:
        if cost is not None:
            fixed_sum += cost
    if fixed_sum > JS_MAX_SAFE_INTEGER:
        raise ValueError(
            f"Tổng chi phí cố định chiến dịch ({fixed_sum}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
        )

    # 3. Expected commission
    exp_comm = None
    if base_vnd is not None and rate_bps is not None and expected_attributed_orders is not None:
        gross_num = base_vnd * rate_bps * expected_attributed_orders
        exp_comm = (2 * gross_num + 10_000) // 20_000
        if exp_comm > JS_MAX_SAFE_INTEGER:
            raise ValueError(
                f"Tổng hoa hồng dự kiến ({exp_comm}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
            )

    # 4. Expected variable cost
    exp_var = None
    if variable_cost_per_attributed_order_vnd is not None and expected_attributed_orders is not None:
        exp_var = variable_cost_per_attributed_order_vnd * expected_attributed_orders
        if exp_var > JS_MAX_SAFE_INTEGER:
            raise ValueError(
                f"Tổng chi phí biến đổi dự kiến ({exp_var}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
            )

    # 5. Total expected campaign cost
    total_cost = fixed_sum + (exp_var or 0)
    if total_cost > JS_MAX_SAFE_INTEGER:
        raise ValueError(
            f"Tổng chi phí chiến dịch dự kiến ({total_cost}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
        )

    # 6. Expected contribution magnitude
    if exp_comm is not None or exp_var is not None or fixed_sum > 0:
        net_contrib = (exp_comm or 0) - total_cost
        if abs(net_contrib) > JS_MAX_SAFE_INTEGER:
            raise ValueError(
                f"Độ lớn lợi nhuận đóng góp dự kiến ({abs(net_contrib)}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
            )


class EconomicsScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    commission_rate_bps: Optional[int] = Field(None, ge=0, le=10000)
    commission_base_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    use_observed_price: bool = False
    sample_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    content_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    promotion_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    variable_cost_per_attributed_order_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    expected_attributed_orders: Optional[int] = Field(None, ge=0, le=10**6)
    is_default: bool = False

    @field_validator("commission_rate_bps", mode="before")
    @classmethod
    def validate_rate_bps(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        if isinstance(v, float) and not v.is_integer():
            raise ValueError("Tỷ lệ hoa hồng tối đa 2 chữ số thập phân (bội số của 0.01% / 1 basis point).")
        return int(v)

    @model_validator(mode="after")
    def validate_safe_integer_totals(self) -> "EconomicsScenarioCreate":
        validate_safe_integer_monetary_outputs(
            base_vnd=self.commission_base_vnd,
            rate_bps=self.commission_rate_bps,
            sample_cost_vnd=self.sample_cost_vnd,
            content_cost_vnd=self.content_cost_vnd,
            promotion_cost_vnd=self.promotion_cost_vnd,
            variable_cost_per_attributed_order_vnd=self.variable_cost_per_attributed_order_vnd,
            expected_attributed_orders=self.expected_attributed_orders,
        )
        return self


class EconomicsScenarioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    commission_rate_bps: Optional[int] = Field(None, ge=0, le=10000)
    commission_base_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    sample_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    content_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    promotion_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    variable_cost_per_attributed_order_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    expected_attributed_orders: Optional[int] = Field(None, ge=0, le=10**6)

    @field_validator("commission_rate_bps", mode="before")
    @classmethod
    def validate_rate_bps(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        if isinstance(v, float) and not v.is_integer():
            raise ValueError("Tỷ lệ hoa hồng tối đa 2 chữ số thập phân (bội số của 0.01% / 1 basis point).")
        return int(v)

    @model_validator(mode="after")
    def validate_safe_integer_totals(self) -> "EconomicsScenarioUpdate":
        validate_safe_integer_monetary_outputs(
            base_vnd=self.commission_base_vnd,
            rate_bps=self.commission_rate_bps,
            sample_cost_vnd=self.sample_cost_vnd,
            content_cost_vnd=self.content_cost_vnd,
            promotion_cost_vnd=self.promotion_cost_vnd,
            variable_cost_per_attributed_order_vnd=self.variable_cost_per_attributed_order_vnd,
            expected_attributed_orders=self.expected_attributed_orders,
        )
        return self


class EconomicsScenarioDuplicate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class DerivedEconomics(BaseModel):
    commission_per_order_vnd: Optional[int] = None
    fixed_campaign_cost_vnd: Optional[int] = None
    contribution_per_order_vnd: Optional[int] = None
    break_even_orders: Optional[int] = None
    expected_commission_vnd: Optional[int] = None
    expected_variable_cost_vnd: Optional[int] = None
    expected_contribution_vnd: Optional[int] = None
    return_on_cost_ratio: Optional[float] = None


class EconomicsScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    name: str
    commission_rate_bps: Optional[int] = None
    commission_base_vnd: Optional[int] = None
    commission_base_source: str
    commission_base_observed_at: Optional[datetime] = None
    sample_cost_vnd: Optional[int] = None
    content_cost_vnd: Optional[int] = None
    promotion_cost_vnd: Optional[int] = None
    variable_cost_per_attributed_order_vnd: Optional[int] = None
    expected_attributed_orders: Optional[int] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime
    derived: DerivedEconomics
