from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.commercial import (
    ComercioCreate,
    ComercioResponse,
    HoldingCreate,
    HoldingResponse,
    SucursalCreate,
    SucursalResponse,
    TerminalCreate,
    TerminalResponse,
    TerminalUpdate,
)
from app.services import commercial_service

router = APIRouter(prefix="/api", tags=["Commercial"])


# --- Holdings ---

@router.post("/holdings", response_model=HoldingResponse, status_code=201)
async def create_holding(
    data: HoldingCreate,
    session: AsyncSession = Depends(get_db),
) -> HoldingResponse:
    return await commercial_service.create_holding(session, data)


@router.get("/holdings", response_model=List[HoldingResponse])
async def list_holdings(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[HoldingResponse]:
    return await commercial_service.get_holdings(session, skip=skip, limit=limit)


@router.get("/holdings/{holding_id}", response_model=HoldingResponse)
async def get_holding(
    holding_id: int,
    session: AsyncSession = Depends(get_db),
) -> HoldingResponse:
    return await commercial_service.get_holding(session, holding_id)


# --- Comercios ---

@router.post("/comercios", response_model=ComercioResponse, status_code=201)
async def create_comercio(
    data: ComercioCreate,
    session: AsyncSession = Depends(get_db),
) -> ComercioResponse:
    return await commercial_service.create_comercio(session, data)


@router.get("/comercios", response_model=List[ComercioResponse])
async def list_comercios(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[ComercioResponse]:
    return await commercial_service.get_comercios(session, skip=skip, limit=limit)


@router.get("/comercios/{comercio_id}", response_model=ComercioResponse)
async def get_comercio(
    comercio_id: int,
    session: AsyncSession = Depends(get_db),
) -> ComercioResponse:
    return await commercial_service.get_comercio(session, comercio_id)


# --- Sucursales ---

@router.post("/sucursales", response_model=SucursalResponse, status_code=201)
async def create_sucursal(
    data: SucursalCreate,
    session: AsyncSession = Depends(get_db),
) -> SucursalResponse:
    return await commercial_service.create_sucursal(session, data)


@router.get("/sucursales", response_model=List[SucursalResponse])
async def list_sucursales(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[SucursalResponse]:
    return await commercial_service.get_sucursales(session, skip=skip, limit=limit)


# --- Terminales ---

@router.post("/terminales", response_model=TerminalResponse, status_code=201)
async def create_terminal(
    data: TerminalCreate,
    session: AsyncSession = Depends(get_db),
) -> TerminalResponse:
    return await commercial_service.create_terminal(session, data)


@router.get("/terminales", response_model=List[TerminalResponse])
async def list_terminales(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[TerminalResponse]:
    return await commercial_service.get_terminales(session, skip=skip, limit=limit)


@router.patch("/terminales/{terminal_id}", response_model=TerminalResponse)
async def update_terminal(
    terminal_id: int,
    data: TerminalUpdate,
    session: AsyncSession = Depends(get_db),
) -> TerminalResponse:
    return await commercial_service.update_terminal(session, terminal_id, data)
