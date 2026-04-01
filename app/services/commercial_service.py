from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.commercial import Comercio, Holding, Sucursal, Terminal
from app.schemas.commercial import (
    ComercioCreate,
    HoldingCreate,
    SucursalCreate,
    TerminalCreate,
    TerminalUpdate,
)


# --- Holdings ---

async def get_holdings(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Holding]:
    stmt = select(Holding).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_holding(session: AsyncSession, holding_id: int) -> Holding:
    holding = await session.get(Holding, holding_id)
    if not holding:
        raise NotFoundError(f"Holding {holding_id} not found")
    return holding


async def create_holding(session: AsyncSession, data: HoldingCreate) -> Holding:
    stmt = select(Holding).where(Holding.rut_holding == data.rut_holding)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise ConflictError(f"Holding with rut_holding '{data.rut_holding}' already exists")
    holding = Holding(
        nombre=data.nombre,
        rut_holding=data.rut_holding,
        segmento=data.segmento,
    )
    session.add(holding)
    await session.flush()
    await session.refresh(holding)
    return holding


# --- Comercios ---

async def get_comercios(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Comercio]:
    stmt = select(Comercio).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_comercio(session: AsyncSession, comercio_id: int) -> Comercio:
    comercio = await session.get(Comercio, comercio_id)
    if not comercio:
        raise NotFoundError(f"Comercio {comercio_id} not found")
    return comercio


async def create_comercio(session: AsyncSession, data: ComercioCreate) -> Comercio:
    stmt = select(Comercio).where(Comercio.rut_comercio == data.rut_comercio)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise ConflictError(f"Comercio with rut_comercio '{data.rut_comercio}' already exists")
    comercio = Comercio(
        rut_comercio=data.rut_comercio,
        nombre_fantasia=data.nombre_fantasia,
        holding_id=data.holding_id,
        external_id=data.external_id,
        mcc=data.mcc,
    )
    session.add(comercio)
    await session.flush()
    await session.refresh(comercio)
    return comercio


# --- Sucursales ---

async def get_sucursales(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Sucursal]:
    stmt = select(Sucursal).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_sucursal(session: AsyncSession, data: SucursalCreate) -> Sucursal:
    # Verify comercio exists
    comercio = await session.get(Comercio, data.comercio_id)
    if not comercio:
        raise NotFoundError(f"Comercio {data.comercio_id} not found")
    sucursal = Sucursal(
        comercio_id=data.comercio_id,
        nombre=data.nombre,
        direccion=data.direccion,
    )
    session.add(sucursal)
    await session.flush()
    await session.refresh(sucursal)
    return sucursal


# --- Terminales ---

async def get_terminales(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Terminal]:
    stmt = select(Terminal).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_terminal(session: AsyncSession, data: TerminalCreate) -> Terminal:
    sucursal = await session.get(Sucursal, data.sucursal_id)
    if not sucursal:
        raise NotFoundError(f"Sucursal {data.sucursal_id} not found")
    terminal = Terminal(
        sucursal_id=data.sucursal_id,
        external_terminal_id=data.external_terminal_id,
        fecha_adquisicion=data.fecha_adquisicion,
        estado=data.estado,
    )
    session.add(terminal)
    await session.flush()
    await session.refresh(terminal)
    return terminal


async def update_terminal(session: AsyncSession, terminal_id: int, data: TerminalUpdate) -> Terminal:
    terminal = await session.get(Terminal, terminal_id)
    if not terminal:
        raise NotFoundError(f"Terminal {terminal_id} not found")
    terminal.estado = data.estado
    await session.flush()
    await session.refresh(terminal)
    return terminal
