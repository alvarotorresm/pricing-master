from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.mdr import MDRTarifa, MDRTarifaAsignacion
from app.schemas.mdr import MDRTarifaAsignacionCreate, MDRTarifaCreate


async def get_mdr_tarifas(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> List[MDRTarifa]:
    stmt = select(MDRTarifa).where(MDRTarifa.activa == True).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_mdr_tarifa(session: AsyncSession, data: MDRTarifaCreate) -> MDRTarifa:
    tarifa = MDRTarifa(
        nombre=data.nombre,
        valor_fijo_uf=data.valor_fijo_uf,
        valor_variable_pct=data.valor_variable_pct,
        descripcion=data.descripcion,
        vigente_desde=data.vigente_desde,
        activa=True,
    )
    session.add(tarifa)
    await session.flush()
    await session.refresh(tarifa)
    return tarifa


async def get_mdr_tarifa(session: AsyncSession, tarifa_id: int) -> MDRTarifa:
    tarifa = await session.get(MDRTarifa, tarifa_id)
    if not tarifa:
        raise NotFoundError(f"MDRTarifa {tarifa_id} not found")
    return tarifa


async def update_mdr_tarifa(
    session: AsyncSession, tarifa_id: int, data: MDRTarifaCreate
) -> MDRTarifa:
    old = await get_mdr_tarifa(session, tarifa_id)
    # Versioning: close old record
    old.vigente_hasta = data.vigente_desde
    old.activa = False
    # Create new record
    new_tarifa = MDRTarifa(
        nombre=data.nombre,
        valor_fijo_uf=data.valor_fijo_uf,
        valor_variable_pct=data.valor_variable_pct,
        descripcion=data.descripcion,
        vigente_desde=data.vigente_desde,
        activa=True,
    )
    session.add(new_tarifa)
    await session.flush()
    await session.refresh(new_tarifa)
    return new_tarifa


async def create_mdr_asignacion(
    session: AsyncSession, data: MDRTarifaAsignacionCreate
) -> MDRTarifaAsignacion:
    # Verify tarifa exists
    await get_mdr_tarifa(session, data.tarifa_id)
    # Check for overlapping active assignment for the same entity
    stmt = select(MDRTarifaAsignacion).where(
        MDRTarifaAsignacion.entity_type == data.entity_type,
        MDRTarifaAsignacion.entity_id == data.entity_id,
        MDRTarifaAsignacion.fecha_inicio <= (data.fecha_fin or date(9999, 12, 31)),
        or_(
            MDRTarifaAsignacion.fecha_fin.is_(None),
            MDRTarifaAsignacion.fecha_fin >= data.fecha_inicio,
        ),
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise ConflictError(
            f"An active MDR tariff assignment already exists for this entity "
            f"({data.entity_type.value} {data.entity_id}) in the given period"
        )
    asig = MDRTarifaAsignacion(
        tarifa_id=data.tarifa_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        prioridad=data.prioridad,
    )
    session.add(asig)
    await session.flush()
    await session.refresh(asig, ["tarifa"])
    return asig


async def get_mdr_asignacion(
    session: AsyncSession, entity_type: str, entity_id: int
) -> Optional[MDRTarifaAsignacion]:
    today = date.today()
    stmt = (
        select(MDRTarifaAsignacion)
        .where(
            MDRTarifaAsignacion.entity_type == entity_type,
            MDRTarifaAsignacion.entity_id == entity_id,
            MDRTarifaAsignacion.fecha_inicio <= today,
            or_(
                MDRTarifaAsignacion.fecha_fin.is_(None),
                MDRTarifaAsignacion.fecha_fin >= today,
            ),
        )
        .order_by(MDRTarifaAsignacion.prioridad.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    asig = result.scalar_one_or_none()
    if asig:
        await session.refresh(asig, ["tarifa"])
    return asig


async def deactivate_mdr_asignacion(session: AsyncSession, asig_id: int) -> None:
    asig = await session.get(MDRTarifaAsignacion, asig_id)
    if not asig:
        raise NotFoundError(f"MDRTarifaAsignacion {asig_id} not found")
    asig.fecha_fin = date.today()
    await session.flush()
