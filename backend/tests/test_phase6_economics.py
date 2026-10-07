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

    # Exact rational contribution regression vector:
    # base = 105 VND, rate = 1000 bps (10.0%), variable = 10 VND, fixed = 1 VND
    # Presentation-rounded commission would be round(10.5) = 11 VND -> contrib = 1 VND -> ceil(1/1) = 1 (WRONG!)
    # Exact rational: contrib_num = 105 * 1000 - 10 * 10,000 = 5,000
    # cost_num = 1 * 10,000 = 10,000 -> ceil(10,000 / 5,000) = 2 (CORRECT, NEVER 1!)
    assert calculate_break_even_orders(105, 1_000, 10, 1) == 2

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


# ==============================================================================
# Workstream 2: Data Model, Concurrency & Default Scenario Invariant Tests
# ==============================================================================

import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, OperationalError
from pydantic import ValidationError

from app.db.base import Base
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.quarantine import QuarantinedProduct
from app.models.system_metadata import SystemMetadata
from app.models.economics_scenario import EconomicsScenario
from app.schemas.economics import (
    EconomicsScenarioCreate,
    EconomicsScenarioUpdate,
)
from app.services.economics_service import EconomicsService


@pytest.fixture
def p6_db(tmp_path: Path):
    """Isolated file-backed database session for Phase 6 tests."""
    db_file = tmp_path / "p6_test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"timeout": 10.0})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(SystemMetadata(key="portable_backup_compatibility_version", value="3"))

    prod = Product(
        platform="tiktok_shop",
        external_product_id="prod_p6_001",
        title="Test Product Economics",
        first_seen_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    session.add(prod)
    session.flush()

    # Quarantined product
    prod_q = Product(
        platform="tiktok_shop",
        external_product_id="prod_p6_quarantine",
        title="Quarantined Product",
        first_seen_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    session.add(prod_q)
    session.flush()
    session.add(QuarantinedProduct(product_id=prod_q.id, reason="Test quarantine"))

    # Initial snapshot for prod
    snap = ProductSnapshot(
        product_id=prod.id,
        price=150_000.4,
        sold_count=5000,
        commission_rate=0.20,
        captured_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    session.add(snap)
    session.commit()

    yield session, engine, prod, prod_q

    session.close()
    engine.dispose()


def test_p6_ac_01_strict_domain_separation(p6_db):
    """
    P6-AC-01: Creating or modifying economics scenarios has zero effect
    on product discovery, metadata, or market tracking.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    initial_title = prod.title
    initial_seen = prod.first_seen_at

    svc.create_scenario(
        prod.id,
        EconomicsScenarioCreate(
            name="Conservative",
            commission_rate_bps=1000,
            commission_base_vnd=100_000,
        ),
    )

    reloaded_prod = session.get(Product, prod.id)
    assert reloaded_prod.title == initial_title
    assert reloaded_prod.first_seen_at == initial_seen


def test_p6_ac_02_attribution_inference_prohibition(p6_db):
    """
    P6-AC-02: Sold count or sales velocity changes do not alter scenario calculations.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    res = svc.create_scenario(
        prod.id,
        EconomicsScenarioCreate(
            name="Baseline",
            commission_rate_bps=1000,
            commission_base_vnd=100_000,
            expected_attributed_orders=50,
        ),
    )
    comm_1 = res["derived"]["commission_per_order_vnd"]
    exp_1 = res["derived"]["expected_commission_vnd"]

    # Ingest a new snapshot with 10x sold count
    new_snap = ProductSnapshot(
        product_id=prod.id,
        price=150_000.0,
        sold_count=50_000,
        captured_at=datetime.now(timezone.utc),
    )
    session.add(new_snap)
    session.commit()

    res_after = svc.get_scenario(prod.id, res["id"])
    assert res_after["derived"]["commission_per_order_vnd"] == comm_1
    assert res_after["derived"]["expected_commission_vnd"] == exp_1


def test_p6_ac_03_manual_first_source_baseline(p6_db):
    """
    P6-AC-03: ProductSnapshot.commission_rate is never automatically used as calculation authority.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    # prod has snapshot with commission_rate=0.20 (20%), but scenario does not set commission_rate_bps
    res = svc.create_scenario(
        prod.id,
        EconomicsScenarioCreate(
            name="No Rate",
            commission_base_vnd=100_000,
            commission_rate_bps=None,
        ),
    )
    assert res["commission_rate_bps"] is None
    assert res["derived"]["commission_per_order_vnd"] is None


def test_p6_ac_04_single_table_persistence(p6_db):
    """
    P6-AC-04: Exactly one new table economics_scenarios is added.
    """
    _, engine, _, _ = p6_db
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "economics_scenarios" in tables
    assert "economics_history" not in tables
    assert "commission_observations" not in tables


def test_p6_ac_05_numeric_types_safe_integer_bounds():
    """
    P6-AC-05: Pydantic schemas enforce bounds: money <= 10^11, bps <= 10,000, orders <= 10^6.
    """
    # Negative money rejected
    with pytest.raises(ValidationError):
        EconomicsScenarioCreate(name="Bad", sample_cost_vnd=-1)

    # Money exceeding 10^11 rejected
    with pytest.raises(ValidationError):
        EconomicsScenarioCreate(name="Bad", sample_cost_vnd=100_000_000_001)

    # Bps exceeding 10,000 rejected
    with pytest.raises(ValidationError):
        EconomicsScenarioCreate(name="Bad", commission_rate_bps=10001)

    # Orders exceeding 1,000,000 rejected
    with pytest.raises(ValidationError):
        EconomicsScenarioCreate(name="Bad", expected_attributed_orders=1_000_001)

    # Fractional basis points rejected (e.g. 12.345% -> 1234.5 bps)
    with pytest.raises(ValidationError, match="bội số của 0.01%"):
        EconomicsScenarioCreate(name="Bad", commission_rate_bps=1234.5)


def test_p6_ac_06_null_preservation(p6_db):
    """
    P6-AC-06: Explicit 0 is preserved as 0; omitted/null is preserved as NULL.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    res = svc.create_scenario(
        prod.id,
        EconomicsScenarioCreate(
            name="Explicit Zero",
            sample_cost_vnd=0,
            content_cost_vnd=None,
        ),
    )
    assert res["sample_cost_vnd"] == 0
    assert res["content_cost_vnd"] is None


def test_p6_ac_07_unique_scenario_name_per_product(p6_db):
    """
    P6-AC-07: Unique name per product. Recreating duplicate name raises HTTP 409 Conflict.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    svc.create_scenario(prod.id, EconomicsScenarioCreate(name="Target Plan"))

    with pytest.raises(HTTPException) as exc_info:
        svc.create_scenario(prod.id, EconomicsScenarioCreate(name="Target Plan"))
    assert exc_info.value.status_code == 409
    assert "Tên kịch bản đã tồn tại" in exc_info.value.detail


def test_p6_ac_08_quarantined_product_exclusion(p6_db):
    """
    P6-AC-08: Quarantined products cannot have economics scenarios created or retrieved.
    """
    session, engine, _, prod_q = p6_db
    svc = EconomicsService(session)

    with pytest.raises(HTTPException) as exc_create:
        svc.create_scenario(prod_q.id, EconomicsScenarioCreate(name="Quarantine Test"))
    assert exc_create.value.status_code == 400
    assert "quarantine" in exc_create.value.detail

    with pytest.raises(HTTPException) as exc_list:
        svc.list_scenarios(prod_q.id)
    assert exc_list.value.status_code == 400


def test_p6_ac_09_to_15_default_scenario_lifecycle(p6_db):
    """
    P6-AC-09..15: Default scenario invariant and deterministic promotion lifecycle.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    # AC-09: 0 scenarios -> 0 defaults
    assert len(svc.list_scenarios(prod.id)) == 0

    # AC-11 & AC-10: First scenario is auto-default
    s1 = svc.create_scenario(prod.id, EconomicsScenarioCreate(name="Plan A"))
    assert s1["is_default"] is True

    # AC-12: Subsequent scenario defaults to is_default = false
    s2 = svc.create_scenario(prod.id, EconomicsScenarioCreate(name="Plan B"))
    assert s2["is_default"] is False

    # Create third scenario
    s3 = svc.create_scenario(prod.id, EconomicsScenarioCreate(name="Plan C"))
    assert s3["is_default"] is False

    # Exactly 1 default exists
    scenarios = svc.list_scenarios(prod.id)
    assert sum(1 for s in scenarios if s["is_default"]) == 1

    # AC-13: Atomic default toggling: promote Plan B
    s2_promoted = svc.set_default(prod.id, s2["id"])
    assert s2_promoted["is_default"] is True
    scenarios = svc.list_scenarios(prod.id)
    assert sum(1 for s in scenarios if s["is_default"]) == 1
    assert next(s for s in scenarios if s["id"] == s1["id"])["is_default"] is False
    assert next(s for s in scenarios if s["id"] == s2["id"])["is_default"] is True

    # AC-14: Delete current default (Plan B).
    # Oldest remaining by (created_at ASC, id ASC) is Plan A.
    svc.delete_scenario(prod.id, s2["id"])
    scenarios = svc.list_scenarios(prod.id)
    assert len(scenarios) == 2
    assert sum(1 for s in scenarios if s["is_default"]) == 1
    # Plan A must be promoted
    assert next(s for s in scenarios if s["id"] == s1["id"])["is_default"] is True
    assert next(s for s in scenarios if s["id"] == s3["id"])["is_default"] is False

    # Delete non-default Plan C
    svc.delete_scenario(prod.id, s3["id"])
    scenarios = svc.list_scenarios(prod.id)
    assert len(scenarios) == 1
    assert scenarios[0]["is_default"] is True

    # AC-15: Delete final scenario Plan A -> 0 scenarios, 0 defaults
    svc.delete_scenario(prod.id, s1["id"])
    scenarios = svc.list_scenarios(prod.id)
    assert len(scenarios) == 0


def test_p6_ac_16_database_partial_unique_index_enforcement(p6_db):
    """
    P6-AC-16: SQLite partial unique index uq_economics_scenarios_product_default
    prevents committing multiple defaults at SQL level.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    s1 = svc.create_scenario(prod.id, EconomicsScenarioCreate(name="SQL Def 1"))
    assert s1["is_default"] is True

    # Attempt raw SQL insert of second default for prod.id
    now = datetime.now(timezone.utc).isoformat()
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO economics_scenarios (product_id, name, is_default, commission_base_source, created_at, updated_at) "
                f"VALUES ({prod.id}, 'SQL Def 2', 1, 'user_entered', '{now}', '{now}')"
            )
        )
        session.commit()
    session.rollback()


# ==============================================================================
# Concurrency 8 Cases (Table 8.3)
# ==============================================================================

def test_concurrency_case_1_concurrent_first_scenario_create(p6_db):
    """
    Case 1: Thread 1 and Thread 2 simultaneously create Scenario A and Scenario B
    on a product with 0 scenarios. Exactly 1 default must exist.
    """
    session, engine, prod, _ = p6_db
    Session = sessionmaker(bind=engine)
    barrier = threading.Barrier(2)

    def worker(name: str):
        s = Session()
        try:
            svc = EconomicsService(s)
            barrier.wait()
            svc.create_scenario(prod.id, EconomicsScenarioCreate(name=name))
        finally:
            s.close()

    t1 = threading.Thread(target=worker, args=("Concurrent A",))
    t2 = threading.Thread(target=worker, args=("Concurrent B",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Verify state
    s = Session()
    svc = EconomicsService(s)
    scenarios = svc.list_scenarios(prod.id)
    s.close()

    assert len(scenarios) == 2
    assert sum(1 for sc in scenarios if sc["is_default"]) == 1


def test_concurrency_case_2_concurrent_create_requesting_default(p6_db):
    """
    Case 2: Thread 1 and Thread 2 simultaneously create Scenario A (is_default=True)
    and Scenario B (is_default=True). Exactly 1 default exists.
    """
    session, engine, prod, _ = p6_db
    Session = sessionmaker(bind=engine)
    barrier = threading.Barrier(2)

    def worker(name: str):
        s = Session()
        try:
            svc = EconomicsService(s)
            barrier.wait()
            svc.create_scenario(prod.id, EconomicsScenarioCreate(name=name, is_default=True))
        finally:
            s.close()

    t1 = threading.Thread(target=worker, args=("Req Def A",))
    t2 = threading.Thread(target=worker, args=("Req Def B",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    s = Session()
    svc = EconomicsService(s)
    scenarios = svc.list_scenarios(prod.id)
    s.close()

    assert len(scenarios) == 2
    assert sum(1 for sc in scenarios if sc["is_default"]) == 1


def test_concurrency_case_3_simultaneous_set_default(p6_db):
    """
    Case 3: Thread 1 sets Scenario A as default; Thread 2 sets Scenario B as default.
    Exactly 1 default exists.
    """
    session, engine, prod, _ = p6_db
    prod_id = prod.id
    svc = EconomicsService(session)
    sa = svc.create_scenario(prod_id, EconomicsScenarioCreate(name="SetDef A"))
    sb = svc.create_scenario(prod_id, EconomicsScenarioCreate(name="SetDef B"))
    session.close()

    Session = sessionmaker(bind=engine)
    barrier = threading.Barrier(2)

    def worker(scenario_id: int):
        s = Session()
        try:
            w_svc = EconomicsService(s)
            barrier.wait()
            w_svc.set_default(prod_id, scenario_id)
        finally:
            s.close()

    t1 = threading.Thread(target=worker, args=(sa["id"],))
    t2 = threading.Thread(target=worker, args=(sb["id"],))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    s = Session()
    w_svc = EconomicsService(s)
    scenarios = w_svc.list_scenarios(prod_id)
    s.close()

    assert len(scenarios) == 2
    assert sum(1 for sc in scenarios if sc["is_default"]) == 1


def test_concurrency_case_4_set_default_racing_delete_current_default(p6_db):
    """
    Case 4: Thread 1 sets Scenario B as default; Thread 2 deletes Scenario A (current default).
    Exactly 1 default exists.
    """
    session, engine, prod, _ = p6_db
    prod_id = prod.id
    svc = EconomicsService(session)
    sa = svc.create_scenario(prod_id, EconomicsScenarioCreate(name="Def A"))
    sb = svc.create_scenario(prod_id, EconomicsScenarioCreate(name="NonDef B"))
    sc = svc.create_scenario(prod_id, EconomicsScenarioCreate(name="NonDef C"))
    session.close()

    Session = sessionmaker(bind=engine)
    barrier = threading.Barrier(2)

    def worker_set(scenario_id: int):
        s = Session()
        try:
            w_svc = EconomicsService(s)
            barrier.wait()
            w_svc.set_default(prod_id, scenario_id)
        except Exception:
            pass
        finally:
            s.close()

    def worker_del(scenario_id: int):
        s = Session()
        try:
            w_svc = EconomicsService(s)
            barrier.wait()
            w_svc.delete_scenario(prod_id, scenario_id)
        except Exception:
            pass
        finally:
            s.close()

    t1 = threading.Thread(target=worker_set, args=(sb["id"],))
    t2 = threading.Thread(target=worker_del, args=(sa["id"],))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    s = Session()
    w_svc = EconomicsService(s)
    scenarios = w_svc.list_scenarios(prod_id)
    s.close()

    assert len(scenarios) == 2
    assert sum(1 for item in scenarios if item["is_default"]) == 1


def test_concurrency_case_5_delete_default_racing_scenario_create(p6_db):
    """
    Case 5: Thread 1 deletes sole Scenario A; Thread 2 creates Scenario B.
    Exactly 1 default exists.
    """
    session, engine, prod, _ = p6_db
    prod_id = prod.id
    svc = EconomicsService(session)
    sa = svc.create_scenario(prod_id, EconomicsScenarioCreate(name="Sole A"))
    session.close()

    Session = sessionmaker(bind=engine)
    barrier = threading.Barrier(2)

    def worker_del(scenario_id: int):
        s = Session()
        try:
            w_svc = EconomicsService(s)
            barrier.wait()
            w_svc.delete_scenario(prod_id, scenario_id)
        finally:
            s.close()

    def worker_create(name: str):
        s = Session()
        try:
            w_svc = EconomicsService(s)
            barrier.wait()
            w_svc.create_scenario(prod_id, EconomicsScenarioCreate(name=name))
        finally:
            s.close()

    t1 = threading.Thread(target=worker_del, args=(sa["id"],))
    t2 = threading.Thread(target=worker_create, args=("New B",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    s = Session()
    w_svc = EconomicsService(s)
    scenarios = w_svc.list_scenarios(prod_id)
    s.close()

    assert len(scenarios) >= 1
    assert sum(1 for item in scenarios if item["is_default"]) == 1


def test_concurrency_case_6_injected_rollback_on_promotion(p6_db):
    """
    Case 6: Delete Scenario A (default); inject exception before promoting Scenario B.
    Entire transaction rolls back. Scenario A remains default.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)
    sa = svc.create_scenario(prod.id, EconomicsScenarioCreate(name="Def A"))
    sb = svc.create_scenario(prod.id, EconomicsScenarioCreate(name="NonDef B"))

    # Mock flush to raise exception during delete_scenario
    with patch.object(session, "flush", side_effect=RuntimeError("Simulated DB Crash")):
        with pytest.raises(RuntimeError, match="Simulated DB Crash"):
            svc.delete_scenario(prod.id, sa["id"])

    # Reload and assert transaction rolled back
    scenarios = svc.list_scenarios(prod.id)
    assert len(scenarios) == 2
    assert next(s for s in scenarios if s["id"] == sa["id"])["is_default"] is True


def test_concurrency_case_7_direct_partial_unique_index_violation(p6_db):
    """
    Case 7: Direct raw SQL insert attempting two is_default = 1 rows raises IntegrityError.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)
    svc.create_scenario(prod.id, EconomicsScenarioCreate(name="First Default"))

    now = datetime.now(timezone.utc).isoformat()
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                f"INSERT INTO economics_scenarios (product_id, name, is_default, commission_base_source, created_at, updated_at) "
                f"VALUES ({prod.id}, 'Illegal Default', 1, 'user_entered', '{now}', '{now}')"
            )
        )
        session.commit()
    session.rollback()


def test_concurrency_case_8_retry_exhaustion_mapping(p6_db):
    """
    Case 8: Simulate permanent lock exhaustion. Service returns HTTP 409 Conflict.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    with patch.object(session, "connection", side_effect=OperationalError("locked", {}, None)):
        with pytest.raises(HTTPException) as exc_info:
            svc.create_scenario(prod.id, EconomicsScenarioCreate(name="Exhausted Lock"))
        assert exc_info.value.status_code == 409
        assert "Cơ sở dữ liệu đang bận" in exc_info.value.detail


# ==============================================================================
# Provenance, Proxy & Rebase Tests (AC-27..31)
# ==============================================================================

def test_p6_ac_27_observed_price_proxy_freezing(p6_db):
    """
    P6-AC-27: Choosing use_observed_price=True freezes latest snapshot price and timestamp.
    Supplying manual base when use_observed_price=True is rejected with HTTP 422.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    # prod has snapshot with price 150_000.4 VND
    res = svc.create_scenario(
        prod.id,
        EconomicsScenarioCreate(
            name="Proxy Freeze",
            use_observed_price=True,
            commission_base_vnd=None,
        ),
    )
    assert res["commission_base_vnd"] == 150_000
    assert res["commission_base_source"] == "observed_price_proxy"
    assert res["commission_base_observed_at"] is not None

    # Mutual exclusion error
    with pytest.raises(HTTPException) as exc_conflict:
        svc.create_scenario(
            prod.id,
            EconomicsScenarioCreate(
                name="Conflict",
                use_observed_price=True,
                commission_base_vnd=200_000,
            ),
        )
    assert exc_conflict.value.status_code == 422


def test_p6_ac_28_proxy_immutability_against_crawlers(p6_db):
    """
    P6-AC-28: Ingesting a new snapshot with different price does not mutate existing frozen proxy.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    res = svc.create_scenario(
        prod.id,
        EconomicsScenarioCreate(
            name="Frozen Proxy",
            use_observed_price=True,
        ),
    )
    frozen_base = res["commission_base_vnd"]

    # Crawler ingests snapshot with 300,000 VND
    new_snap = ProductSnapshot(
        product_id=prod.id,
        price=300_000.0,
        captured_at=datetime.now(timezone.utc),
    )
    session.add(new_snap)
    session.commit()

    reloaded = svc.get_scenario(prod.id, res["id"])
    assert reloaded["commission_base_vnd"] == frozen_base


def test_p6_ac_29_provenance_reset_on_manual_edit(p6_db):
    """
    P6-AC-29: Editing commission_base_vnd resets source to 'user_entered' and clears timestamp.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    res = svc.create_scenario(
        prod.id,
        EconomicsScenarioCreate(
            name="Proxy Before Edit",
            use_observed_price=True,
        ),
    )
    assert res["commission_base_source"] == "observed_price_proxy"
    assert res["commission_base_observed_at"] is not None

    updated = svc.update_scenario(
        prod.id,
        res["id"],
        EconomicsScenarioUpdate(commission_base_vnd=250_000),
    )
    assert updated["commission_base_vnd"] == 250_000
    assert updated["commission_base_source"] == "user_entered"
    assert updated["commission_base_observed_at"] is None


def test_p6_ac_30_deterministic_duplicate_semantics(p6_db):
    """
    P6-AC-30: Cloned scenario defaults to is_default = false and copies assumptions.
    Duplicate name raises HTTP 409.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    res = svc.create_scenario(
        prod.id,
        EconomicsScenarioCreate(
            name="Original Plan",
            commission_rate_bps=1200,
            commission_base_vnd=200_000,
            sample_cost_vnd=50_000,
        ),
    )
    assert res["is_default"] is True

    cloned = svc.duplicate_scenario(prod.id, res["id"], "Cloned Plan")
    assert cloned["name"] == "Cloned Plan"
    assert cloned["commission_rate_bps"] == 1200
    assert cloned["commission_base_vnd"] == 200_000
    assert cloned["sample_cost_vnd"] == 50_000
    assert cloned["is_default"] is False

    # Duplicate with same name raises 409
    with pytest.raises(HTTPException) as exc_info:
        svc.duplicate_scenario(prod.id, res["id"], "Original Plan")
    assert exc_info.value.status_code == 409


def test_p6_ac_31_explicit_price_rebase(p6_db):
    """
    P6-AC-31: rebase-price endpoint updates commission_base_vnd and timestamp to latest snapshot.
    """
    session, engine, prod, _ = p6_db
    svc = EconomicsService(session)

    res = svc.create_scenario(
        prod.id,
        EconomicsScenarioCreate(
            name="To Rebase",
            commission_base_vnd=100_000,
        ),
    )
    assert res["commission_base_source"] == "user_entered"

    # Add newer snapshot with 220,000 VND
    new_captured = datetime.now(timezone.utc)
    new_snap = ProductSnapshot(
        product_id=prod.id,
        price=220_000.0,
        captured_at=new_captured,
    )
    session.add(new_snap)
    session.commit()

    rebased = svc.rebase_price(prod.id, res["id"])
    assert rebased["commission_base_vnd"] == 220_000
    assert rebased["commission_base_source"] == "observed_price_proxy"
    assert rebased["commission_base_observed_at"] is not None


# ==============================================================================
# REST API Integration Tests (Workstream 4)
# ==============================================================================

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db


@pytest.fixture
def test_client(p6_db):
    session, _, _, _ = p6_db

    def override_get_db():
        try:
            yield session
        finally:
            pass

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    if original_override:
        app.dependency_overrides[get_db] = original_override
    else:
        app.dependency_overrides.pop(get_db, None)


def test_api_economics_crud_lifecycle(test_client: TestClient, p6_db):
    """
    Test full REST API lifecycle on /api/products/{id}/economics:
    POST create, GET list, GET single, PATCH update, POST duplicate,
    POST set-default, POST rebase-price, DELETE.
    """
    _, _, prod, _ = p6_db
    p_id = prod.id

    # 1. POST create first scenario (auto default)
    r_create = test_client.post(
        f"/api/products/{p_id}/economics",
        json={
            "name": "API Scenario 1",
            "commission_rate_bps": 1500,
            "commission_base_vnd": 200_000,
            "sample_cost_vnd": 50_000,
            "content_cost_vnd": 100_000,
            "promotion_cost_vnd": 150_000,
            "variable_cost_per_attributed_order_vnd": 5_000,
            "expected_attributed_orders": 100,
        },
    )
    assert r_create.status_code == 201
    d1 = r_create.json()
    assert d1["name"] == "API Scenario 1"
    assert d1["is_default"] is True
    assert d1["derived"]["commission_per_order_vnd"] == 30_000
    assert d1["derived"]["break_even_orders"] == 12
    s1_id = d1["id"]

    # 2. GET list scenarios
    r_list = test_client.get(f"/api/products/{p_id}/economics")
    assert r_list.status_code == 200
    items = r_list.json()
    assert len(items) == 1
    assert items[0]["id"] == s1_id

    # 3. GET single scenario
    r_get = test_client.get(f"/api/products/{p_id}/economics/{s1_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == s1_id

    # 4. PATCH update assumptions
    r_patch = test_client.patch(
        f"/api/products/{p_id}/economics/{s1_id}",
        json={
            "commission_base_vnd": 250_000,
            "expected_attributed_orders": 200,
        },
    )
    assert r_patch.status_code == 200
    d_patch = r_patch.json()
    assert d_patch["commission_base_vnd"] == 250_000
    assert d_patch["commission_base_source"] == "user_entered"
    # Derived reflects 250k base * 15% = 37,500
    assert d_patch["derived"]["commission_per_order_vnd"] == 37_500

    # 5. POST duplicate
    r_dup = test_client.post(
        f"/api/products/{p_id}/economics/{s1_id}/duplicate",
        json={"name": "API Scenario 2 Cloned"},
    )
    assert r_dup.status_code == 201
    d_dup = r_dup.json()
    assert d_dup["name"] == "API Scenario 2 Cloned"
    assert d_dup["is_default"] is False
    s2_id = d_dup["id"]

    # 6. POST set-default
    r_def = test_client.post(f"/api/products/{p_id}/economics/{s2_id}/set-default")
    assert r_def.status_code == 200
    assert r_def.json()["is_default"] is True

    # 7. POST rebase-price
    r_rebase = test_client.post(f"/api/products/{p_id}/economics/{s1_id}/rebase-price")
    assert r_rebase.status_code == 200
    assert r_rebase.json()["commission_base_source"] == "observed_price_proxy"

    # 8. DELETE scenario
    r_del = test_client.delete(f"/api/products/{p_id}/economics/{s2_id}")
    assert r_del.status_code == 204

    # Verify s1 is promoted back to default
    r_after = test_client.get(f"/api/products/{p_id}/economics/{s1_id}")
    assert r_after.status_code == 200
    assert r_after.json()["is_default"] is True


def test_api_economics_error_mappings(test_client: TestClient, p6_db):
    """
    Test standard HTTP error status code mappings:
    400, 404, 409, 422.
    """
    _, _, prod, prod_q = p6_db
    p_id = prod.id
    q_id = prod_q.id

    # 404: Non-existent product
    r_404 = test_client.get("/api/products/999999/economics")
    assert r_404.status_code == 404

    # 400: Quarantined product
    r_400 = test_client.get(f"/api/products/{q_id}/economics")
    assert r_400.status_code == 400
    assert "quarantine" in r_400.json()["detail"]

    # 409: Duplicate name
    test_client.post(f"/api/products/{p_id}/economics", json={"name": "Duplicate Me"})
    r_409 = test_client.post(f"/api/products/{p_id}/economics", json={"name": "Duplicate Me"})
    assert r_409.status_code == 409

    # 422: Mutual exclusion (use_observed_price=True with manual base)
    r_422 = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Invalid Base", "use_observed_price": True, "commission_base_vnd": 100_000},
    )
    assert r_422.status_code == 422


def test_api_diagnostics_includes_economics(test_client: TestClient):
    """
    Diagnostics endpoint includes safe table count for economics_scenarios.
    """
    res = test_client.get("/api/diagnostics")
    assert res.status_code == 200
    data = res.json()
    assert "database" in data
    assert "table_counts" in data["database"]
    assert "economics_scenarios" in data["database"]["table_counts"]
    assert isinstance(data["database"]["table_counts"]["economics_scenarios"], int)


# ==============================================================================
# Remediation: Safe-Integer Contracts & Focused Provenance Tests
# ==============================================================================

def test_safe_integer_max_boundary_and_rejections(test_client: TestClient, p6_db):
    """
    Verifies JavaScript safe-integer contract (Number.MAX_SAFE_INTEGER = 9,007,199,254,740,991):
    - Field-level max boundaries: accepted at bound, rejected at bound + 1.
    - Derived totals (variable_cost * expected_orders): accepted within safe integer,
      rejected with HTTP 422 when product exceeds Number.MAX_SAFE_INTEGER.
    """
    _, _, prod, _ = p6_db
    p_id = prod.id

    # 1. Field bounds: commission_rate_bps (max 10,000)
    r_bps_ok = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Bps Max", "commission_rate_bps": 10_000},
    )
    assert r_bps_ok.status_code == 201

    r_bps_over = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Bps Over", "commission_rate_bps": 10_001},
    )
    assert r_bps_over.status_code == 422

    # 2. Field bounds: commission_base_vnd (max 10^11 = 100,000,000,000)
    r_base_ok = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Base Max", "commission_base_vnd": 100_000_000_000},
    )
    assert r_base_ok.status_code == 201

    r_base_over = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Base Over", "commission_base_vnd": 100_000_000_001},
    )
    assert r_base_over.status_code == 422

    # 3. Field bounds: sample_cost_vnd (max 10^11)
    r_sample_ok = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Sample Max", "sample_cost_vnd": 100_000_000_000},
    )
    assert r_sample_ok.status_code == 201

    r_sample_over = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Sample Over", "sample_cost_vnd": 100_000_000_001},
    )
    assert r_sample_over.status_code == 422

    # 4. Field bounds: variable_cost_per_attributed_order_vnd (max 10^11)
    r_var_ok = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Var Max", "variable_cost_per_attributed_order_vnd": 100_000_000_000},
    )
    assert r_var_ok.status_code == 201

    r_var_over = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Var Over", "variable_cost_per_attributed_order_vnd": 100_000_000_001},
    )
    assert r_var_over.status_code == 422

    # 5. Field bounds: expected_attributed_orders (max 10^6)
    r_ord_ok = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Orders Max", "expected_attributed_orders": 1_000_000},
    )
    assert r_ord_ok.status_code == 201

    r_ord_over = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Orders Over", "expected_attributed_orders": 1_000_001},
    )
    assert r_ord_over.status_code == 422

    # 6. Derived total: variable_cost * expected_orders safe-integer contract
    # Within bound: 90,071,992,547 * 100,000 = 9,007,199,254,700,000 <= 9,007,199,254,740,991
    r_total_ok = test_client.post(
        f"/api/products/{p_id}/economics",
        json={
            "name": "Total Safe OK",
            "variable_cost_per_attributed_order_vnd": 90_071_992_547,
            "expected_attributed_orders": 100_000,
        },
    )
    assert r_total_ok.status_code == 201

    # Over bound: 90,071,992,548 * 100,000 = 9,007,199,254,800,000 > 9,007,199,254,740,991
    r_total_over = test_client.post(
        f"/api/products/{p_id}/economics",
        json={
            "name": "Total Safe Over",
            "variable_cost_per_attributed_order_vnd": 90_071_992_548,
            "expected_attributed_orders": 100_000,
        },
    )
    assert r_total_over.status_code == 422
    assert "giới hạn an toàn" in r_total_over.json()["detail"][0]["msg"]

    # 7. Update scenario safe-integer enforcement
    sc_id = r_total_ok.json()["id"]
    r_patch_over = test_client.patch(
        f"/api/products/{p_id}/economics/{sc_id}",
        json={"variable_cost_per_attributed_order_vnd": 90_071_992_548},
    )
    assert r_patch_over.status_code == 422


def test_pure_engine_safe_integer_clamping():
    """
    Pure analytics engine defensively clamps / returns None for numbers exceeding JS_MAX_SAFE_INTEGER.
    """
    from app.analytics.economics import (
        JS_MAX_SAFE_INTEGER,
        calculate_expected_campaign_economics,
        calculate_break_even_orders,
        calculate_commission_per_order,
    )
    # Beyond safe integer returns None for expected variable cost
    exp_comm, exp_var, exp_contrib, ret = calculate_expected_campaign_economics(
        base_vnd=100_000,
        rate_bps=1000,
        variable_cost_per_order_vnd=90_071_992_548,
        fixed_campaign_cost_vnd=0,
        expected_orders=100_000,
    )
    assert exp_var is None
    assert exp_contrib is None

    # Within safe integer succeeds
    exp_comm2, exp_var2, exp_contrib2, ret2 = calculate_expected_campaign_economics(
        base_vnd=100_000,
        rate_bps=1000,
        variable_cost_per_order_vnd=90_071_992_547,
        fixed_campaign_cost_vnd=0,
        expected_orders=100_000,
    )
    assert exp_var2 == 9_007_199_254_700_000
    assert exp_var2 <= JS_MAX_SAFE_INTEGER


def test_focused_provenance_rules(test_client: TestClient, p6_db):
    """
    Focused verification of all 5 provenance rules:
    1. Client cannot forge provenance or source timestamp.
    2. Manual edit clears timestamp and sets source to 'user_entered'.
    3. Proxy price and timestamp come from the exact same observation.
    4. PATCH cannot change is_default.
    5. Crawler commission rate is not economics authority.
    """
    session, engine, prod, _ = p6_db
    p_id = prod.id

    # Rule 1: Client cannot forge provenance or timestamp
    r_forge = test_client.post(
        f"/api/products/{p_id}/economics",
        json={
            "name": "Forged Provenance",
            "commission_base_vnd": 180_000,
            "commission_base_source": "observed_price_proxy",
            "commission_base_observed_at": "2020-01-01T00:00:00Z",
        },
    )
    assert r_forge.status_code == 201
    d_forge = r_forge.json()
    # Server forced user_entered and ignored forged proxy fields
    assert d_forge["commission_base_source"] == "user_entered"
    assert d_forge["commission_base_observed_at"] is None

    # Rule 2: Manual edit clears timestamp
    r_proxy = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Proxy Valid", "use_observed_price": True},
    )
    assert r_proxy.status_code == 201
    proxy_id = r_proxy.json()["id"]
    assert r_proxy.json()["commission_base_source"] == "observed_price_proxy"
    assert r_proxy.json()["commission_base_observed_at"] is not None

    r_edit = test_client.patch(
        f"/api/products/{p_id}/economics/{proxy_id}",
        json={"commission_base_vnd": 210_000},
    )
    assert r_edit.status_code == 200
    d_edit = r_edit.json()
    assert d_edit["commission_base_source"] == "user_entered"
    assert d_edit["commission_base_observed_at"] is None

    # Rule 3: Proxy price and timestamp come from the exact same snapshot
    # prod has snapshot with price 150_000.4 VND
    latest_snap = (
        session.query(ProductSnapshot)
        .filter_by(product_id=p_id)
        .order_by(ProductSnapshot.captured_at.desc(), ProductSnapshot.id.desc())
        .first()
    )
    assert latest_snap is not None
    assert r_proxy.json()["commission_base_vnd"] == 150_000
    # Timestamp matches snapshot captured_at
    obs_at = datetime.fromisoformat(r_proxy.json()["commission_base_observed_at"].replace("Z", "+00:00"))
    assert obs_at == latest_snap.captured_at

    # Rule 4: PATCH cannot change is_default
    r_sibling = test_client.post(
        f"/api/products/{p_id}/economics",
        json={"name": "Sibling Not Default"},
    )
    assert r_sibling.status_code == 201
    sib_id = r_sibling.json()["id"]
    assert r_sibling.json()["is_default"] is False

    # Attempt to change is_default via PATCH
    r_patch_def = test_client.patch(
        f"/api/products/{p_id}/economics/{sib_id}",
        json={"is_default": True},
    )
    assert r_patch_def.status_code == 200
    # is_default is untouched!
    assert r_patch_def.json()["is_default"] is False

    # Rule 5: Crawler snapshot commission rate is not economics authority
    new_snap = ProductSnapshot(
        product_id=p_id,
        price=160_000.0,
        commission_rate=45.0,  # 45% crawler observation
        captured_at=datetime.now(timezone.utc),
    )
    session.add(new_snap)
    session.commit()

    # Verify scenario commission_rate_bps was NOT modified by crawler
    sc_check = test_client.get(f"/api/products/{p_id}/economics/{proxy_id}").json()
    # Was None, remains None (or user's value), never 4500 bps
    assert sc_check["commission_rate_bps"] is None


