from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EntityType
from app.dependencies import get_db
from app.schemas.mdr import (
    MDRTarifaAsignacionCreate,
    MDRTarifaAsignacionResponse,
    MDRTarifaCreate,
    MDRTarifaResponse,
)
from app.services import mdr_service

router = APIRouter(prefix="/api", tags=["MDR Tarifas"])


@router.get("/mdr-tarifas", response_model=List[MDRTarifaResponse])
async def list_mdr_tarifas(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[MDRTarifaResponse]:
    return await mdr_service.get_mdr_tarifas(session, skip=skip, limit=limit)


@router.post("/mdr-tarifas", response_model=MDRTarifaResponse, status_code=201)
async def create_mdr_tarifa(
    data: MDRTarifaCreate,
    session: AsyncSession = Depends(get_db),
) -> MDRTarifaResponse:
    return await mdr_service.create_mdr_tarifa(session, data)


@router.get("/mdr-tarifas/{tarifa_id}", response_model=MDRTarifaResponse)
async def get_mdr_tarifa(
    tarifa_id: int,
    session: AsyncSession = Depends(get_db),
) -> MDRTarifaResponse:
    return await mdr_service.get_mdr_tarifa(session, tarifa_id)


@router.put("/mdr-tarifas/{tarifa_id}", response_model=MDRTarifaResponse)
async def update_mdr_tarifa(
    tarifa_id: int,
    data: MDRTarifaCreate,
    session: AsyncSession = Depends(get_db),
) -> MDRTarifaResponse:
    return await mdr_service.update_mdr_tarifa(session, tarifa_id, data)


@router.post("/mdr-tarifa-asignaciones", response_model=MDRTarifaAsignacionResponse, status_code=201)
async def create_mdr_asignacion(
    data: MDRTarifaAsignacionCreate,
    session: AsyncSession = Depends(get_db),
) -> MDRTarifaAsignacionResponse:
    return await mdr_service.create_mdr_asignacion(session, data)


@router.get("/mdr-tarifa-asignaciones", response_model=Optional[MDRTarifaAsignacionResponse])
async def get_mdr_asignacion(
    entity_type: EntityType,
    entity_id: int,
    session: AsyncSession = Depends(get_db),
) -> Optional[MDRTarifaAsignacionResponse]:
    return await mdr_service.get_mdr_asignacion(session, entity_type, entity_id)


@router.delete("/mdr-tarifa-asignaciones/{asig_id}", status_code=204)
async def deactivate_mdr_asignacion(
    asig_id: int,
    session: AsyncSession = Depends(get_db),
) -> Response:
    await mdr_service.deactivate_mdr_asignacion(session, asig_id)
    return Response(status_code=204)
