from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

JS_MAX_SAFE_INTEGER: int = 9_007_199_254_740_991  # 2^53 - 1


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
        if self.variable_cost_per_attributed_order_vnd is not None and self.expected_attributed_orders is not None:
            total_var = self.variable_cost_per_attributed_order_vnd * self.expected_attributed_orders
            if total_var > JS_MAX_SAFE_INTEGER:
                raise ValueError(
                    f"Tổng chi phí biến đổi dự kiến ({total_var}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
                )
        if (
            self.commission_base_vnd is not None
            and self.commission_rate_bps is not None
            and self.expected_attributed_orders is not None
        ):
            gross_num = self.commission_base_vnd * self.commission_rate_bps * self.expected_attributed_orders
            gross_comm = (2 * gross_num + 10_000) // 20_000
            if gross_comm > JS_MAX_SAFE_INTEGER:
                raise ValueError(
                    f"Tổng hoa hồng dự kiến ({gross_comm}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
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
        if self.variable_cost_per_attributed_order_vnd is not None and self.expected_attributed_orders is not None:
            total_var = self.variable_cost_per_attributed_order_vnd * self.expected_attributed_orders
            if total_var > JS_MAX_SAFE_INTEGER:
                raise ValueError(
                    f"Tổng chi phí biến đổi dự kiến ({total_var}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
                )
        if (
            self.commission_base_vnd is not None
            and self.commission_rate_bps is not None
            and self.expected_attributed_orders is not None
        ):
            gross_num = self.commission_base_vnd * self.commission_rate_bps * self.expected_attributed_orders
            gross_comm = (2 * gross_num + 10_000) // 20_000
            if gross_comm > JS_MAX_SAFE_INTEGER:
                raise ValueError(
                    f"Tổng hoa hồng dự kiến ({gross_comm}) vượt quá giới hạn an toàn JavaScript ({JS_MAX_SAFE_INTEGER})."
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
