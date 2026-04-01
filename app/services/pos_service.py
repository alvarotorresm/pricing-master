from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.pos import POSTarifa, POSTarifaAsignacion
from app.schemas.pos import POSTarifaAsignacionCreate, POSTarifaCreate


async def get_pos_tarifas(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> List[POSTarifa]:
    stmt = select(POSTarifa).where(POSTarifa.activa == True).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_pos_tarifa(session: AsyncSession, data: POSTarifaCreate) -> POSTarifa:
    if data.valor_mensual_uf < Decimal("0.00") or data.valor_mensual_uf > Decimal("1.00"):
        raise BusinessRuleError("valor_mensual_uf must be between 0.00 and 1.00 UF")
    tarifa = POSTarifa(
        nombre=data.nombre,
        valor_mensual_uf=data.valor_mensual_uf,
        descripcion=data.descripcion,
        vigente_desde=data.vigente_desde,
        activa=True,
    )
    session.add(tarifa)
    await session.flush()
    await session.refresh(tarifa)
    return tarifa


async def get_pos_tarifa(session: AsyncSession, tarifa_id: int) -> POSTarifa:
    tarifa = await session.get(POSTarifa, tarifa_id)
    if not tarifa:
        raise NotFoundError(f"POSTarifa {tarifa_id} not found")
    return tarifa


async def update_pos_tarifa(
    session: AsyncSession, tarifa_id: int, data: POSTarifaCreate
) -> POSTarifa:
    if data.valor_mensual_uf < Decimal("0.00") or data.valor_mensual_uf > Decimal("1.00"):
        raise BusinessRuleError("valor_mensual_uf must be between 0.00 and 1.00 UF")
    old = await get_pos_tarifa(session, tarifa_id)
    # Versioning: close old record
    old.vigente_hasta = data.vigente_desde
    old.activa = False
    # Create new record
    new_tarifa = POSTarifa(
        nombre=data.nombre,
        valor_mensual_uf=data.valor_mensual_uf,
        descripcion=data.descripcion,
        vigente_desde=data.vigente_desde,
        activa=True,
    )
    session.add(new_tarifa)
    await session.flush()
    await session.refresh(new_tarifa)
    return new_tarifa


async def create_pos_asignacion(
    session: AsyncSession, data: POSTarifaAsignacionCreate
) -> POSTarifaAsignacion:
    # Verify tarifa exists
    await get_pos_tarifa(session, data.tarifa_id)
    # Check for overlapping active assignment for the same entity
    stmt = select(POSTarifaAsignacion).where(
        POSTarifaAsignacion.entity_type == data.entity_type,
        POSTarifaAsignacion.entity_id == data.entity_id,
        POSTarifaAsignacion.fecha_inicio <= (data.fecha_fin or date(9999, 12, 31)),
        or_(
            POSTarifaAsignacion.fecha_fin.is_(None),
            POSTarifaAsignacion.fecha_fin >= data.fecha_inicio,
        ),
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise ConflictError(
            f"An active POS tariff assignment already exists for this entity "
            f"({data.entity_type.value} {data.entity_id}) in the given period"
        )
    asig = POSTarifaAsignacion(
        tarifa_id=data.tarifa_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        prioridad=data.prioridad,
    )
    session.add(asig)
    await session.flush()
    # Reload with relationship
    await session.refresh(asig, ["tarifa"])
    return asig


async def get_pos_asignacion(
    session: AsyncSession, entity_type: str, entity_id: int
) -> Optional[POSTarifaAsignacion]:
    today = date.today()
    stmt = (
        select(POSTarifaAsignacion)
        .where(
            POSTarifaAsignacion.entity_type == entity_type,
            POSTarifaAsignacion.entity_id == entity_id,
            POSTarifaAsignacion.fecha_inicio <= today,
            or_(
                POSTarifaAsignacion.fecha_fin.is_(None),
                POSTarifaAsignacion.fecha_fin >= today,
            ),
        )
        .order_by(POSTarifaAsignacion.prioridad.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    asig = result.scalar_one_or_none()
    if asig:
        await session.refresh(asig, ["tarifa"])
    return asig


async def deactivate_pos_asignacion(session: AsyncSession, asig_id: int) -> None:
    asig = await session.get(POSTarifaAsignacion, asig_id)
    if not asig:
        raise NotFoundError(f"POSTarifaAsignacion {asig_id} not found")
    asig.fecha_fin = date.today()
    await session.flush()
