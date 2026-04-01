from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EntityType
from app.dependencies import get_db
from app.schemas.pos import (
    POSTarifaAsignacionCreate,
    POSTarifaAsignacionResponse,
    POSTarifaCreate,
    POSTarifaResponse,
)
from app.services import pos_service

router = APIRouter(prefix="/api", tags=["POS Tarifas"])


@router.get("/pos-tarifas", response_model=List[POSTarifaResponse])
async def list_pos_tarifas(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[POSTarifaResponse]:
    return await pos_service.get_pos_tarifas(session, skip=skip, limit=limit)


@router.post("/pos-tarifas", response_model=POSTarifaResponse, status_code=201)
async def create_pos_tarifa(
    data: POSTarifaCreate,
    session: AsyncSession = Depends(get_db),
) -> POSTarifaResponse:
    return await pos_service.create_pos_tarifa(session, data)


@router.get("/pos-tarifas/{tarifa_id}", response_model=POSTarifaResponse)
async def get_pos_tarifa(
    tarifa_id: int,
    session: AsyncSession = Depends(get_db),
) -> POSTarifaResponse:
    return await pos_service.get_pos_tarifa(session, tarifa_id)


@router.put("/pos-tarifas/{tarifa_id}", response_model=POSTarifaResponse)
async def update_pos_tarifa(
    tarifa_id: int,
    data: POSTarifaCreate,
    session: AsyncSession = Depends(get_db),
) -> POSTarifaResponse:
    return await pos_service.update_pos_tarifa(session, tarifa_id, data)


@router.post("/pos-tarifa-asignaciones", response_model=POSTarifaAsignacionResponse, status_code=201)
async def create_pos_asignacion(
    data: POSTarifaAsignacionCreate,
    session: AsyncSession = Depends(get_db),
) -> POSTarifaAsignacionResponse:
    return await pos_service.create_pos_asignacion(session, data)


@router.get("/pos-tarifa-asignaciones", response_model=Optional[POSTarifaAsignacionResponse])
async def get_pos_asignacion(
    entity_type: EntityType,
    entity_id: int,
    session: AsyncSession = Depends(get_db),
) -> Optional[POSTarifaAsignacionResponse]:
    return await pos_service.get_pos_asignacion(session, entity_type, entity_id)


@router.delete("/pos-tarifa-asignaciones/{asig_id}", status_code=204)
async def deactivate_pos_asignacion(
    asig_id: int,
    session: AsyncSession = Depends(get_db),
) -> Response:
    await pos_service.deactivate_pos_asignacion(session, asig_id)
    return Response(status_code=204)
