"""
Pure deterministic Affiliate Economics calculation engine for Phase 6.
Operates exclusively with integer ratio arithmetic and exact ceiling division.
Does NOT pass intermediate calculations through binary float.
"""

from typing import Optional, Dict, Any, NamedTuple
from decimal import Decimal, ROUND_HALF_UP

RATE_SCALE: int = 10_000  # 10,000 bps = 100.00%


class DerivedEconomicsResult(NamedTuple):
    commission_per_order_vnd: Optional[int]
    fixed_campaign_cost_vnd: Optional[int]
    contribution_per_order_vnd: Optional[int]
    break_even_orders: Optional[int]
    expected_commission_vnd: Optional[int]
    expected_variable_cost_vnd: Optional[int]
    expected_contribution_vnd: Optional[int]
    return_on_cost_ratio: Optional[float]


def round_half_up_ratio(numerator: int, denominator: int) -> int:
    """
    Authoritative integer ratio round-half-up policy to nearest integer:
    floor((2*N + D) / (2*D)) for N >= 0, D > 0.
    Eliminates binary floating-point representation artifacts.
    """
    if denominator <= 0:
        raise ValueError("Denominator must be strictly positive")
    if numerator < 0:
        raise ValueError("Numerator must be non-negative for financial amounts")
    return (2 * numerator + denominator) // (2 * denominator)


def normalize_snapshot_price_to_vnd(latest_price: Optional[float]) -> Optional[int]:
    """
    Deliberate single normalization boundary converting legacy ProductSnapshot.price (Float)
    into a whole integer VND proxy.
    """
    if latest_price is None or latest_price <= 0:
        return None
    # Use exact string decimal quantization to whole VND
    d = Decimal(str(latest_price)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(d)


def calculate_commission_per_order(
    base_vnd: Optional[int],
    rate_bps: Optional[int],
) -> Optional[int]:
    """
    Calculates estimated commission per attributable order in whole integer VND.
    Requires both base_vnd and rate_bps to be non-null. Otherwise returns None.
    """
    if base_vnd is None or rate_bps is None:
        return None
    if base_vnd < 0 or rate_bps < 0 or rate_bps > RATE_SCALE:
        return None
    numerator = base_vnd * rate_bps
    return round_half_up_ratio(numerator, RATE_SCALE)


def calculate_fixed_campaign_cost(
    sample_cost_vnd: Optional[int],
    content_cost_vnd: Optional[int],
    promotion_cost_vnd: Optional[int],
) -> Optional[int]:
    """
    Calculates total fixed campaign cost.
    Requires all three components to be non-null (or explicitly 0).
    If any component is None, evaluates to None.
    """
    if sample_cost_vnd is None or content_cost_vnd is None or promotion_cost_vnd is None:
        return None
    if sample_cost_vnd < 0 or content_cost_vnd < 0 or promotion_cost_vnd < 0:
        return None
    return sample_cost_vnd + content_cost_vnd + promotion_cost_vnd


def calculate_contribution_per_order(
    commission_per_order_vnd: Optional[int],
    variable_cost_per_order_vnd: Optional[int],
) -> Optional[int]:
    """
    Calculates unit contribution margin per attributable order in whole VND.
    Requires commission_per_order_vnd and variable_cost_per_order_vnd to be non-null.
    """
    if commission_per_order_vnd is None or variable_cost_per_order_vnd is None:
        return None
    if variable_cost_per_order_vnd < 0:
        return None
    return commission_per_order_vnd - variable_cost_per_order_vnd


def calculate_break_even_orders(
    base_vnd: Optional[int],
    rate_bps: Optional[int],
    variable_cost_per_order_vnd: Optional[int],
    fixed_campaign_cost_vnd: Optional[int],
) -> Optional[int]:
    """
    Calculates break-even attributable order count using exact rational contribution numerator
    and integer ceiling division.
    Does NOT use presentation-rounded commission/order to avoid off-by-one errors.
    Returns None if:
    - fixed_campaign_cost_vnd is None or < 0
    - base_vnd or rate_bps or variable_cost_per_order_vnd is None
    - unit contribution numerator <= 0 (zero or negative contribution margin)
    """
    if (
        fixed_campaign_cost_vnd is None
        or fixed_campaign_cost_vnd < 0
        or base_vnd is None
        or rate_bps is None
        or variable_cost_per_order_vnd is None
        or variable_cost_per_order_vnd < 0
        or base_vnd < 0
        or rate_bps < 0
        or rate_bps > RATE_SCALE
    ):
        return None

    # Exact rational numerator: (base * bps) - (variable_cost * 10,000)
    contrib_num = (base_vnd * rate_bps) - (variable_cost_per_order_vnd * RATE_SCALE)
    if contrib_num <= 0:
        return None

    if fixed_campaign_cost_vnd == 0:
        return 0

    # Exact integer ceiling division: ceil(A / B) = (A + B - 1) // B
    cost_num = fixed_campaign_cost_vnd * RATE_SCALE
    return (cost_num + contrib_num - 1) // contrib_num


def calculate_expected_campaign_economics(
    base_vnd: Optional[int],
    rate_bps: Optional[int],
    variable_cost_per_order_vnd: Optional[int],
    fixed_campaign_cost_vnd: Optional[int],
    expected_orders: Optional[int],
) -> tuple[Optional[int], Optional[int], Optional[int], Optional[float]]:
    """
    Calculates expected campaign metrics if expected_orders is provided.
    Returns:
    (expected_commission_vnd, expected_variable_cost_vnd, expected_contribution_vnd, return_on_cost_ratio)
    """
    if expected_orders is None or expected_orders < 0:
        return (None, None, None, None)

    # 1. Expected gross commission
    if base_vnd is not None and rate_bps is not None and 0 <= rate_bps <= RATE_SCALE and base_vnd >= 0:
        gross_num = base_vnd * rate_bps * expected_orders
        expected_commission_vnd: Optional[int] = round_half_up_ratio(gross_num, RATE_SCALE)
    else:
        expected_commission_vnd = None

    # 2. Expected variable cost
    if variable_cost_per_order_vnd is not None and variable_cost_per_order_vnd >= 0:
        expected_variable_cost_vnd: Optional[int] = variable_cost_per_order_vnd * expected_orders
    else:
        expected_variable_cost_vnd = None

    # 3. Expected net contribution
    if (
        expected_commission_vnd is not None
        and fixed_campaign_cost_vnd is not None
        and expected_variable_cost_vnd is not None
    ):
        expected_contribution_vnd: Optional[int] = (
            expected_commission_vnd - fixed_campaign_cost_vnd - expected_variable_cost_vnd
        )
    else:
        expected_contribution_vnd = None

    # 4. Scenario return on cost ratio
    if (
        expected_contribution_vnd is not None
        and fixed_campaign_cost_vnd is not None
        and expected_variable_cost_vnd is not None
    ):
        total_campaign_cost = fixed_campaign_cost_vnd + expected_variable_cost_vnd
        if total_campaign_cost > 0:
            return_on_cost_ratio: Optional[float] = round(expected_contribution_vnd / total_campaign_cost, 4)
        else:
            return_on_cost_ratio = None
    else:
        return_on_cost_ratio = None

    return (
        expected_commission_vnd,
        expected_variable_cost_vnd,
        expected_contribution_vnd,
        return_on_cost_ratio,
    )


def compute_derived_economics(
    base_vnd: Optional[int],
    rate_bps: Optional[int],
    sample_cost_vnd: Optional[int],
    content_cost_vnd: Optional[int],
    promotion_cost_vnd: Optional[int],
    variable_cost_per_order_vnd: Optional[int],
    expected_orders: Optional[int],
) -> DerivedEconomicsResult:
    """
    Computes all derived metrics deterministically for a scenario.
    """
    comm_order = calculate_commission_per_order(base_vnd, rate_bps)
    fixed_cost = calculate_fixed_campaign_cost(sample_cost_vnd, content_cost_vnd, promotion_cost_vnd)
    contrib_order = calculate_contribution_per_order(comm_order, variable_cost_per_order_vnd)
    break_even = calculate_break_even_orders(base_vnd, rate_bps, variable_cost_per_order_vnd, fixed_cost)
    (
        exp_comm,
        exp_var_cost,
        exp_contrib,
        ret_on_cost,
    ) = calculate_expected_campaign_economics(
        base_vnd, rate_bps, variable_cost_per_order_vnd, fixed_cost, expected_orders
    )

    return DerivedEconomicsResult(
        commission_per_order_vnd=comm_order,
        fixed_campaign_cost_vnd=fixed_cost,
        contribution_per_order_vnd=contrib_order,
        break_even_orders=break_even,
        expected_commission_vnd=exp_comm,
        expected_variable_cost_vnd=exp_var_cost,
        expected_contribution_vnd=exp_contrib,
        return_on_cost_ratio=ret_on_cost,
    )
