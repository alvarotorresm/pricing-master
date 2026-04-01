from __future__ import annotations

from datetime import date
from decimal import Decimal
from math import floor
from typing import Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    BeneficioPOS,
    EntityType,
    MecanismoActivacion,
    TerminalEstado,
    TipoProducto,
)
from app.core.exceptions import NotFoundError
from app.models.commercial import Comercio, Sucursal, Terminal
from app.models.pos import POSTarifaAsignacion
from app.models.promotions import Promotion, PromotionAssignment
from app.models.transactions import TransaccionMensual


async def resolver_pos(terminal_id: int, periodo: date, session: AsyncSession) -> dict:
    # Step 1: Load terminal → sucursal → comercio chain
    terminal = await session.get(Terminal, terminal_id)
    if not terminal:
        raise NotFoundError(f"Terminal {terminal_id} not found")
    sucursal = await session.get(Sucursal, terminal.sucursal_id)
    comercio = await session.get(Comercio, sucursal.comercio_id)

    # Step 2: Get base POS tariff (SUCURSAL > COMERCIO > HOLDING)
    tarifa_base = await _get_base_pos_tarifa(session, terminal, sucursal, comercio, periodo)

    # Step 3: Get active promotion (same hierarchy)
    promo_assignment, entity_type_promo = await _get_active_pos_promotion(
        session, terminal, sucursal, comercio, periodo
    )

    # Step 4: Evaluate activation mechanism
    beneficio_vigente = False
    n_beneficiadas = 0
    if promo_assignment:
        beneficio_vigente, n_beneficiadas = await _evaluate_pos_mechanism(
            session, promo_assignment, terminal, sucursal, comercio, entity_type_promo, periodo
        )

    # Step 5: Calculate final charge
    if tarifa_base:
        base_uf = tarifa_base.tarifa.valor_mensual_uf
    else:
        base_uf = Decimal("0.00")

    if not beneficio_vigente or not promo_assignment:
        cobro = base_uf
    elif promo_assignment.promotion.beneficio_pos == BeneficioPOS.COSTO_CERO:
        cobro = Decimal("0.00")
    else:  # PRECIO_REBAJADO
        cobro = promo_assignment.promotion.valor_cobro_uf

    ahorro = base_uf - cobro

    return {
        "terminal_id": terminal_id,
        "periodo": periodo.strftime("%Y-%m"),
        "tarifa_base": (
            {
                "id": tarifa_base.tarifa.id,
                "nombre": tarifa_base.tarifa.nombre,
                "valor_mensual_uf": base_uf,
            }
            if tarifa_base
            else None
        ),
        "beneficio_aplicado": (
            _format_pos_beneficio(promo_assignment, beneficio_vigente)
            if promo_assignment
            else None
        ),
        "cobro_final_uf": cobro,
        "ahorro_uf": ahorro,
        "n_terminales_beneficiadas": n_beneficiadas,
    }


async def _get_base_pos_tarifa(
    session: AsyncSession,
    terminal: Terminal,
    sucursal: Sucursal,
    comercio: Comercio,
    periodo: date,
) -> Optional[POSTarifaAsignacion]:
    """Returns the most specific active POSTarifaAsignacion for the terminal's period."""
    for entity_type, entity_id in [
        (EntityType.SUCURSAL, terminal.sucursal_id),
        (EntityType.COMERCIO, sucursal.comercio_id),
        (EntityType.HOLDING, comercio.holding_id),
    ]:
        if entity_id is None:
            continue
        stmt = (
            select(POSTarifaAsignacion)
            .join(POSTarifaAsignacion.tarifa)
            .where(
                POSTarifaAsignacion.entity_type == entity_type,
                POSTarifaAsignacion.entity_id == entity_id,
                POSTarifaAsignacion.fecha_inicio <= periodo,
                or_(
                    POSTarifaAsignacion.fecha_fin.is_(None),
                    POSTarifaAsignacion.fecha_fin >= periodo,
                ),
            )
            .order_by(POSTarifaAsignacion.prioridad.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        asig = result.scalar_one_or_none()
        if asig:
            # Eagerly load tarifa relationship
            await session.refresh(asig, ["tarifa"])
            return asig
    return None


async def _get_active_pos_promotion(
    session: AsyncSession,
    terminal: Terminal,
    sucursal: Sucursal,
    comercio: Comercio,
    periodo: date,
) -> Tuple[Optional[PromotionAssignment], Optional[EntityType]]:
    """Returns (PromotionAssignment, EntityType) for the most specific active POS promotion."""
    for entity_type, entity_id in [
        (EntityType.SUCURSAL, terminal.sucursal_id),
        (EntityType.COMERCIO, sucursal.comercio_id),
        (EntityType.HOLDING, comercio.holding_id),
    ]:
        if entity_id is None:
            continue
        stmt = (
            select(PromotionAssignment)
            .join(PromotionAssignment.promotion)
            .where(
                PromotionAssignment.entity_type == entity_type,
                PromotionAssignment.entity_id == entity_id,
                PromotionAssignment.activa == True,
                Promotion.tipo_producto == TipoProducto.POS,
                Promotion.activa == True,
                or_(
                    PromotionAssignment.fecha_inicio.is_(None),
                    PromotionAssignment.fecha_inicio <= periodo,
                ),
                or_(
                    PromotionAssignment.fecha_fin.is_(None),
                    PromotionAssignment.fecha_fin >= periodo,
                ),
            )
            .order_by(PromotionAssignment.prioridad.desc())
        )
        result = await session.execute(stmt)
        assignments = result.scalars().all()
        if assignments:
            # Eagerly load promotion relationship for all
            for a in assignments:
                await session.refresh(a, ["promotion"])
            # Conflict resolution: if any non-stackable, pick highest prioridad; else all
            non_stackable = [a for a in assignments if not a.promotion.is_stackable]
            if non_stackable:
                return max(non_stackable, key=lambda a: a.prioridad), entity_type
            return assignments[0], entity_type
    return None, None


async def _evaluate_pos_mechanism(
    session: AsyncSession,
    promo_assignment: PromotionAssignment,
    terminal: Terminal,
    sucursal: Sucursal,
    comercio: Comercio,
    entity_type: EntityType,
    periodo: date,
) -> Tuple[bool, int]:
    """Returns (is_active: bool, n_benefited: int)"""
    promo = promo_assignment.promotion
    today = date.today()

    if promo.mecanismo_activacion == MecanismoActivacion.ADQUISICION:
        dias = (today - terminal.fecha_adquisicion).days
        return dias <= promo.duracion_dias, 1

    elif promo.mecanismo_activacion == MecanismoActivacion.PERMANENTE_ILIMITADO:
        return True, 0

    elif promo.mecanismo_activacion == MecanismoActivacion.PERMANENTE_LIMITADO:
        count = await _count_active_terminals(session, entity_type, promo_assignment.entity_id)
        return count <= promo.max_terminales, count

    elif promo.mecanismo_activacion == MecanismoActivacion.USO:
        monto = await _get_monto_mes(session, entity_type, promo_assignment.entity_id, periodo)
        tramos = floor(monto / promo.umbral_monto_mm) if promo.umbral_monto_mm else 0
        total_activo = await _count_active_terminals(session, entity_type, promo_assignment.entity_id)
        n_beneficio = min(
            tramos * (promo.pos_por_tramo or 1),
            promo.max_pos_beneficio if promo.max_pos_beneficio is not None else total_activo,
        )
        # Check if THIS terminal ranks within n_beneficio (ordered by fecha_adquisicion ASC)
        terminals_ordered = await _get_terminals_ordered(session, entity_type, promo_assignment.entity_id)
        terminal_ids = [t.id for t in terminals_ordered]
        rank = terminal_ids.index(terminal.id) + 1 if terminal.id in terminal_ids else 999
        return rank <= n_beneficio, n_beneficio

    return False, 0


async def _count_active_terminals(
    session: AsyncSession, entity_type: EntityType, entity_id: int
) -> int:
    if entity_type == EntityType.SUCURSAL:
        stmt = (
            select(func.count())
            .select_from(Terminal)
            .where(Terminal.sucursal_id == entity_id, Terminal.estado == TerminalEstado.ACTIVO)
        )
    elif entity_type == EntityType.COMERCIO:
        stmt = (
            select(func.count())
            .select_from(Terminal)
            .join(Sucursal, Terminal.sucursal_id == Sucursal.id)
            .where(Sucursal.comercio_id == entity_id, Terminal.estado == TerminalEstado.ACTIVO)
        )
    else:  # HOLDING
        stmt = (
            select(func.count())
            .select_from(Terminal)
            .join(Sucursal, Terminal.sucursal_id == Sucursal.id)
            .join(Comercio, Sucursal.comercio_id == Comercio.id)
            .where(Comercio.holding_id == entity_id, Terminal.estado == TerminalEstado.ACTIVO)
        )
    result = await session.execute(stmt)
    return result.scalar_one()


async def _get_terminals_ordered(
    session: AsyncSession, entity_type: EntityType, entity_id: int
):
    if entity_type == EntityType.SUCURSAL:
        stmt = (
            select(Terminal)
            .where(Terminal.sucursal_id == entity_id, Terminal.estado == TerminalEstado.ACTIVO)
            .order_by(Terminal.fecha_adquisicion.asc())
        )
    elif entity_type == EntityType.COMERCIO:
        stmt = (
            select(Terminal)
            .join(Sucursal, Terminal.sucursal_id == Sucursal.id)
            .where(Sucursal.comercio_id == entity_id, Terminal.estado == TerminalEstado.ACTIVO)
            .order_by(Terminal.fecha_adquisicion.asc())
        )
    else:  # HOLDING
        stmt = (
            select(Terminal)
            .join(Sucursal, Terminal.sucursal_id == Sucursal.id)
            .join(Comercio, Sucursal.comercio_id == Comercio.id)
            .where(Comercio.holding_id == entity_id, Terminal.estado == TerminalEstado.ACTIVO)
            .order_by(Terminal.fecha_adquisicion.asc())
        )
    result = await session.execute(stmt)
    return result.scalars().all()


async def _get_monto_mes(
    session: AsyncSession, entity_type: EntityType, entity_id: int, periodo: date
) -> Decimal:
    if entity_type == EntityType.SUCURSAL:
        stmt = select(func.sum(TransaccionMensual.monto_total_mm)).where(
            TransaccionMensual.sucursal_id == entity_id,
            TransaccionMensual.periodo == periodo,
        )
    elif entity_type == EntityType.COMERCIO:
        stmt = (
            select(func.sum(TransaccionMensual.monto_total_mm))
            .join(Sucursal, TransaccionMensual.sucursal_id == Sucursal.id)
            .where(Sucursal.comercio_id == entity_id, TransaccionMensual.periodo == periodo)
        )
    else:  # HOLDING
        stmt = (
            select(func.sum(TransaccionMensual.monto_total_mm))
            .join(Sucursal, TransaccionMensual.sucursal_id == Sucursal.id)
            .join(Comercio, Sucursal.comercio_id == Comercio.id)
            .where(Comercio.holding_id == entity_id, TransaccionMensual.periodo == periodo)
        )
    result = await session.execute(stmt)
    return Decimal(str(result.scalar_one() or 0))


def _format_pos_beneficio(promo_assignment: PromotionAssignment, vigente: bool) -> dict:
    p = promo_assignment.promotion
    return {
        "promotion_id": p.id,
        "tipo_producto": p.tipo_producto,
        "mecanismo_activacion": p.mecanismo_activacion,
        "beneficio_pos": p.beneficio_pos,
        "vigente": vigente,
        "descripcion": p.descripcion,
    }
