from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EntityType, TipoProducto
from app.dependencies import get_db
from app.schemas.promotions import (
    PromotionAssignmentCreate,
    PromotionAssignmentResponse,
    PromotionCreate,
    PromotionResponse,
)
from app.services import promotion_service

router = APIRouter(prefix="/api", tags=["Promotions"])


@router.get("/promotions", response_model=List[PromotionResponse])
async def list_promotions(
    tipo_producto: Optional[TipoProducto] = None,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[PromotionResponse]:
    return await promotion_service.get_promotions(
        session, tipo_producto=tipo_producto, skip=skip, limit=limit
    )


@router.post("/promotions", response_model=PromotionResponse, status_code=201)
async def create_promotion(
    data: PromotionCreate,
    session: AsyncSession = Depends(get_db),
) -> PromotionResponse:
    return await promotion_service.create_promotion(session, data)


@router.post("/promotion-assignments", response_model=PromotionAssignmentResponse, status_code=201)
async def create_promotion_assignment(
    data: PromotionAssignmentCreate,
    session: AsyncSession = Depends(get_db),
) -> PromotionAssignmentResponse:
    return await promotion_service.create_promotion_assignment(session, data)


@router.get("/promotion-assignments", response_model=List[PromotionAssignmentResponse])
async def list_promotion_assignments(
    entity_type: EntityType,
    entity_id: int,
    session: AsyncSession = Depends(get_db),
) -> List[PromotionAssignmentResponse]:
    return await promotion_service.get_promotion_assignments(session, entity_type, entity_id)


@router.delete("/promotion-assignments/{asig_id}", status_code=204)
async def deactivate_promotion_assignment(
    asig_id: int,
    session: AsyncSession = Depends(get_db),
) -> Response:
    await promotion_service.deactivate_promotion_assignment(session, asig_id)
    return Response(status_code=204)
