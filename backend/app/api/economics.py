from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.economics_service import EconomicsService
from app.schemas.economics import (
    EconomicsScenarioCreate,
    EconomicsScenarioUpdate,
    EconomicsScenarioDuplicate,
    EconomicsScenarioResponse,
)

router = APIRouter(prefix="/products/{product_id}/economics", tags=["Economics"])


@router.get("", response_model=List[EconomicsScenarioResponse])
def list_economics_scenarios(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    List all scenarios for a product with read-time calculated derived economics.
    Query budget: <= 2 SQL queries total; zero N+1.
    """
    service = EconomicsService(db)
    return service.list_scenarios(product_id)


@router.post("", response_model=EconomicsScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_economics_scenario(
    product_id: int,
    payload: EconomicsScenarioCreate,
    db: Session = Depends(get_db),
):
    """
    Creates a new economics scenario for a product adhering to default scenario invariants.
    """
    service = EconomicsService(db)
    return service.create_scenario(product_id, payload)


@router.get("/{scenario_id}", response_model=EconomicsScenarioResponse)
def get_economics_scenario(
    product_id: int,
    scenario_id: int,
    db: Session = Depends(get_db),
):
    """
    Gets a single scenario with read-time calculated derived metrics.
    """
    service = EconomicsService(db)
    return service.get_scenario(product_id, scenario_id)


@router.patch("/{scenario_id}", response_model=EconomicsScenarioResponse)
def update_economics_scenario(
    product_id: int,
    scenario_id: int,
    payload: EconomicsScenarioUpdate,
    db: Session = Depends(get_db),
):
    """
    Updates scenario assumptions.
    Modifying commission_base_vnd automatically resets source to 'user_entered' and clears timestamp.
    """
    service = EconomicsService(db)
    return service.update_scenario(product_id, scenario_id, payload)


@router.post("/{scenario_id}/duplicate", response_model=EconomicsScenarioResponse, status_code=status.HTTP_201_CREATED)
def duplicate_economics_scenario(
    product_id: int,
    scenario_id: int,
    payload: EconomicsScenarioDuplicate,
    db: Session = Depends(get_db),
):
    """
    Duplicates an existing scenario.
    Cloned scenario always defaults to is_default = false.
    """
    service = EconomicsService(db)
    return service.duplicate_scenario(product_id, scenario_id, payload.name)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_economics_scenario(
    product_id: int,
    scenario_id: int,
    db: Session = Depends(get_db),
):
    """
    Deletes an economics scenario.
    If default scenario is deleted and alternatives remain, atomically promotes
    the oldest remaining scenario ordered by (created_at ASC, id ASC).
    """
    service = EconomicsService(db)
    service.delete_scenario(product_id, scenario_id)
    return None


@router.post("/{scenario_id}/set-default", response_model=EconomicsScenarioResponse)
def set_default_economics_scenario(
    product_id: int,
    scenario_id: int,
    db: Session = Depends(get_db),
):
    """
    Atomically sets target scenario as the sole default scenario for the product.
    """
    service = EconomicsService(db)
    return service.set_default(product_id, scenario_id)


@router.post("/{scenario_id}/rebase-price", response_model=EconomicsScenarioResponse)
def rebase_price_economics_scenario(
    product_id: int,
    scenario_id: int,
    db: Session = Depends(get_db),
):
    """
    Explicitly captures and freezes the latest observed snapshot price into the scenario.
    """
    service = EconomicsService(db)
    return service.rebase_price(product_id, scenario_id)
