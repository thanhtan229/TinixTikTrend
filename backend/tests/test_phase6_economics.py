"""
Unit tests for Phase 6 Affiliate Economics calculation engine.
Validates integer ratio rounding, pure calculation formulas, exact ceiling division,
and strict null propagation trees.
"""

import pytest
from app.analytics.economics import (
    round_half_up_ratio,
    normalize_snapshot_price_to_vnd,
    calculate_commission_per_order,
    calculate_fixed_campaign_cost,
    calculate_contribution_per_order,
    calculate_break_even_orders,
    calculate_expected_campaign_economics,
    compute_derived_economics,
    RATE_SCALE,
)


def test_p6_ac_20_exact_integer_ratio_rounding_boundaries():
    """
    P6-AC-20: Test exact integer ratio round-half-up to nearest whole VND.
    Formula: (2*N + D) // (2*D).
    Must not use binary float or bankers rounding.
    """
    # Exact .5 boundary cases (odd and even integers must both round UP)
    # 10.5 -> 11
    assert round_half_up_ratio(105, 10) == 11
    # 11.5 -> 12 (bankers rounding would round to 12; test 12.5 -> 13 where bankers would round to 12)
    assert round_half_up_ratio(115, 10) == 12
    assert round_half_up_ratio(125, 10) == 13
    assert round_half_up_ratio(135, 10) == 14

    # Below .5 boundary: 10.49 -> 10
    assert round_half_up_ratio(1049, 100) == 10

    # Above .5 boundary: 10.51 -> 11
    assert round_half_up_ratio(1051, 100) == 11

    # Zero boundary: 0 / 10000 -> 0
    assert round_half_up_ratio(0, 10000) == 0

    # Large financial values without 64-bit overflow or precision loss
    # 99,999,999,995 / 10 -> 100,000,000,000
    assert round_half_up_ratio(999_999_999_995, 10) == 100_000_000_000
    # 9,999_999_999_995 / 10 -> 1,000,000,000,000
    assert round_half_up_ratio(9_999_999_999_995, 10) == 1_000_000_000_000

    # Invalid arguments
    with pytest.raises(ValueError, match="strictly positive"):
        round_half_up_ratio(100, 0)
    with pytest.raises(ValueError, match="non-negative"):
        round_half_up_ratio(-50, 10)


def test_p6_ac_21_commission_per_order_formula():
    """
    P6-AC-21: Commission per order formula: round_half_up_ratio(base * bps, 10,000).
    Requires both inputs; missing input evaluates to None.
    """
    # 100,000 VND @ 1,000 bps (10.00%) = 10,000 VND
    assert calculate_commission_per_order(100_000, 1_000) == 10_000

    # 125,000 VND @ 1,250 bps (12.50%) = 15,625 VND
    assert calculate_commission_per_order(125_000, 1_250) == 15_625

    # 199,000 VND @ 1,500 bps (15.00%) = 29,850 VND
    assert calculate_commission_per_order(199_000, 1_500) == 29_850

    # Fractional VND rounding: 155,555 VND @ 1,000 bps = 15,555.5 -> 15,556 VND
    assert calculate_commission_per_order(155_555, 1_000) == 15_556

    # 0 bps -> 0 VND
    assert calculate_commission_per_order(100_000, 0) == 0

    # 0 base -> 0 VND
    assert calculate_commission_per_order(0, 1_000) == 0

    # Null propagation
    assert calculate_commission_per_order(None, 1_000) is None
    assert calculate_commission_per_order(100_000, None) is None
    assert calculate_commission_per_order(None, None) is None

    # Out of bounds
    assert calculate_commission_per_order(-100, 1_000) is None
    assert calculate_commission_per_order(100_000, -10) is None
    assert calculate_commission_per_order(100_000, 10_001) is None


def test_p6_ac_22_fixed_campaign_cost_null_propagation():
    """
    P6-AC-22: Total fixed campaign cost = sample + content + promotion.
    Evaluated only when all three are non-null (or explicitly 0).
    Any unknown component yields None (unknown != 0).
    """
    # All present
    assert calculate_fixed_campaign_cost(50_000, 100_000, 200_000) == 350_000

    # Explicit zeros are valid
    assert calculate_fixed_campaign_cost(0, 0, 0) == 0
    assert calculate_fixed_campaign_cost(50_000, 0, 0) == 50_000
    assert calculate_fixed_campaign_cost(0, 100_000, 0) == 100_000

    # Missing sample cost -> None
    assert calculate_fixed_campaign_cost(None, 100_000, 200_000) is None

    # Missing content cost -> None
    assert calculate_fixed_campaign_cost(50_000, None, 200_000) is None

    # Missing promotion cost -> None
    assert calculate_fixed_campaign_cost(50_000, 100_000, None) is None

    # All missing -> None
    assert calculate_fixed_campaign_cost(None, None, None) is None

    # Negative inputs -> None
    assert calculate_fixed_campaign_cost(-10, 0, 0) is None


def test_p6_ac_23_contribution_margin_per_order_formula():
    """
    P6-AC-23: Unit contribution margin = commission/order - variable_cost/order.
    Requires calculated commission and variable cost; otherwise None.
    """
    # 10,000 commission - 2,000 variable = 8,000 contribution
    assert calculate_contribution_per_order(10_000, 2_000) == 8_000

    # 10,000 commission - 0 variable = 10,000 contribution
    assert calculate_contribution_per_order(10_000, 0) == 10_000

    # Negative contribution when variable exceeds commission
    assert calculate_contribution_per_order(5_000, 7_000) == -2_000

    # Null propagation
    assert calculate_contribution_per_order(None, 2_000) is None
    assert calculate_contribution_per_order(10_000, None) is None
    assert calculate_contribution_per_order(None, None) is None

    # Negative variable cost -> None
    assert calculate_contribution_per_order(10_000, -500) is None


def test_p6_ac_24_break_even_attributable_orders_exact_math():
    """
    P6-AC-24: Break-even attributable orders uses exact integer ceiling division:
    ceil(fixed_campaign_cost * 10,000 / contrib_num).
    """
    # Exact division: Fixed = 100,000 VND; Base = 100,000 VND; Rate = 1,000 bps (10k); Variable = 0
    # Contrib numerator = 100,000 * 1,000 - 0 = 100,000,000
    # Cost numerator = 100,000 * 10,000 = 1,000,000,000
    # Break even = 1,000,000,000 / 100,000,000 = 10 orders
    assert calculate_break_even_orders(100_000, 1_000, 0, 100_000) == 10

    # Fixed = 100,000 VND; Base = 100,000 VND; Rate = 1,000 bps (10k); Variable = 5,000 VND (5k contrib)
    # Contrib num = 100,000,000 - 50,000,000 = 50,000,000
    # Break even = 1,000,000,000 / 50,000,000 = 20 orders
    assert calculate_break_even_orders(100_000, 1_000, 5_000, 100_000) == 20

    # Ceiling division case: Fixed = 100,000 VND; Base = 100,000 VND; Rate = 300 bps (3,000 VND contrib)
    # Contrib num = 30,000,000
    # Cost num = 1,000,000,000
    # 1,000,000,000 / 30,000,000 = 33.333... -> ceil is 34 orders
    assert calculate_break_even_orders(100_000, 300, 0, 100_000) == 34

    # Fixed cost = 0 -> 0 orders to break even
    assert calculate_break_even_orders(100_000, 1_000, 0, 0) == 0

    # Zero or negative contribution margin yields None
    # Base 100k @ 500 bps = 5,000 VND commission; Variable = 5,000 VND -> contrib_num = 0 -> None
    assert calculate_break_even_orders(100_000, 500, 5_000, 100_000) is None
    # Variable = 6,000 VND -> contrib_num < 0 -> None
    assert calculate_break_even_orders(100_000, 500, 6_000, 100_000) is None

    # Null propagation when any required assumption is missing
    assert calculate_break_even_orders(None, 1_000, 0, 100_000) is None
    assert calculate_break_even_orders(100_000, None, 0, 100_000) is None
    assert calculate_break_even_orders(100_000, 1_000, None, 100_000) is None
    assert calculate_break_even_orders(100_000, 1_000, 0, None) is None


def test_p6_ac_25_expected_campaign_economics():
    """
    P6-AC-25: Expected campaign economics evaluated only when expected_attributed_orders is non-null.
    """
    # 100 expected orders; Base 100,000 VND @ 1,000 bps (10k); Var 2k; Fixed 350k
    # Expected gross comm: 100 * 10k = 1,000,000 VND
    # Expected var cost: 100 * 2k = 200,000 VND
    # Expected net contrib: 1,000,000 - 350,000 - 200,000 = 450,000 VND
    # Total cost: 350,000 + 200,000 = 550,000 VND
    # Return on cost: 450,000 / 550,000 = 0.8182 (+81.82%)
    (
        exp_comm,
        exp_var_cost,
        exp_contrib,
        ret_on_cost,
    ) = calculate_expected_campaign_economics(
        base_vnd=100_000,
        rate_bps=1_000,
        variable_cost_per_order_vnd=2_000,
        fixed_campaign_cost_vnd=350_000,
        expected_orders=100,
    )
    assert exp_comm == 1_000_000
    assert exp_var_cost == 200_000
    assert exp_contrib == 450_000
    assert ret_on_cost == 0.8182

    # Negative net contribution (campaign loss scenario)
    (
        exp_comm_loss,
        exp_var_loss,
        exp_contrib_loss,
        ret_on_cost_loss,
    ) = calculate_expected_campaign_economics(
        base_vnd=100_000,
        rate_bps=1_000,
        variable_cost_per_order_vnd=2_000,
        fixed_campaign_cost_vnd=1_500_000,
        expected_orders=100,
    )
    assert exp_comm_loss == 1_000_000
    assert exp_var_loss == 200_000
    assert exp_contrib_loss == -700_000
    # Total cost = 1.7M; Return on cost = -700k / 1.7M = -0.4118 (-41.18%)
    assert ret_on_cost_loss == -0.4118

    # When expected_orders is None, all expected metrics are None
    assert calculate_expected_campaign_economics(
        base_vnd=100_000,
        rate_bps=1_000,
        variable_cost_per_order_vnd=2_000,
        fixed_campaign_cost_vnd=350_000,
        expected_orders=None,
    ) == (None, None, None, None)

    # Missing fixed cost: expected commission and variable cost still exist, but net contribution is None
    (
        exp_comm_nofix,
        exp_var_nofix,
        exp_contrib_nofix,
        ret_on_cost_nofix,
    ) = calculate_expected_campaign_economics(
        base_vnd=100_000,
        rate_bps=1_000,
        variable_cost_per_order_vnd=2_000,
        fixed_campaign_cost_vnd=None,
        expected_orders=100,
    )
    assert exp_comm_nofix == 1_000_000
    assert exp_var_nofix == 200_000
    assert exp_contrib_nofix is None
    assert ret_on_cost_nofix is None


def test_normalize_snapshot_price_to_vnd_boundary():
    """
    Test single deliberate normalization boundary from snapshot Float to integer VND.
    """
    assert normalize_snapshot_price_to_vnd(150_000.0) == 150_000
    assert normalize_snapshot_price_to_vnd(150_000.4) == 150_000
    assert normalize_snapshot_price_to_vnd(150_000.5) == 150_001
    assert normalize_snapshot_price_to_vnd(150_000.6) == 150_001
    assert normalize_snapshot_price_to_vnd(None) is None
    assert normalize_snapshot_price_to_vnd(0.0) is None
    assert normalize_snapshot_price_to_vnd(-500.0) is None


def test_compute_derived_economics_comprehensive():
    """
    Validates complete scenario evaluation with full assumptions.
    """
    derived = compute_derived_economics(
        base_vnd=200_000,
        rate_bps=1_500,  # 15% -> 30,000 VND
        sample_cost_vnd=50_000,
        content_cost_vnd=100_000,
        promotion_cost_vnd=150_000,  # Fixed = 300,000 VND
        variable_cost_per_order_vnd=5_000,  # Contrib = 25,000 VND
        expected_orders=50,  # Break-even = 300k / 25k = 12 orders
    )
    assert derived.commission_per_order_vnd == 30_000
    assert derived.fixed_campaign_cost_vnd == 300_000
    assert derived.contribution_per_order_vnd == 25_000
    assert derived.break_even_orders == 12
    assert derived.expected_commission_vnd == 1_500_000
    assert derived.expected_variable_cost_vnd == 250_000
    assert derived.expected_contribution_vnd == 950_000
    assert derived.return_on_cost_ratio == round(950_000 / 550_000, 4)
