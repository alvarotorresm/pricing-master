from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    BeneficioMDR,
    EntityType,
    MecanismoActivacion,
    TerminalEstado,
    TipoProducto,
)
from app.core.exceptions import NotFoundError
from app.models.commercial import Comercio, Sucursal, Terminal
from app.models.mdr import MDRTarifaAsignacion
from app.models.promotions import Promotion, PromotionAssignment
from app.models.transactions import TransaccionMensual


async def resolver_mdr(terminal_id: int, periodo: date, session: AsyncSession) -> dict:
    # Step 1: Load terminal → sucursal → comercio chain
    terminal = await session.get(Terminal, terminal_id)
    if not terminal:
        raise NotFoundError(f"Terminal {terminal_id} not found")
    sucursal = await session.get(Sucursal, terminal.sucursal_id)
    comercio = await session.get(Comercio, sucursal.comercio_id)

    # Step 2: Get base MDR tariff (SUCURSAL > COMERCIO > HOLDING)
    tasa_base = await _get_base_mdr_tarifa(session, terminal, sucursal, comercio, periodo)

    # Step 3: Get active MDR promotion (same hierarchy)
    promo_assignment, entity_type_promo = await _get_active_mdr_promotion(
        session, terminal, sucursal, comercio, periodo
    )

    # Step 4: Evaluate activation mechanism
    beneficio_vigente = False
    if promo_assignment:
        beneficio_vigente = await _evaluate_mdr_mechanism(
            session, promo_assignment, terminal, sucursal, comercio, entity_type_promo, periodo
        )

    # Step 5: Calculate final MDR rates
    base_fijo = tasa_base.tarifa.valor_fijo_uf if tasa_base else None
    base_variable = tasa_base.tarifa.valor_variable_pct if tasa_base else None

    if not beneficio_vigente or not promo_assignment:
        fijo_final = base_fijo
        variable_final = base_variable
    else:
        promo = promo_assignment.promotion
        if promo.beneficio_mdr == BeneficioMDR.FIJO:
            fijo_final = promo.valor_fijo_uf
            variable_final = base_variable
        elif promo.beneficio_mdr == BeneficioMDR.VARIABLE:
            fijo_final = base_fijo
            variable_final = promo.valor_variable_pct
        else:  # MIXTO
            fijo_final = promo.valor_fijo_uf
            variable_final = promo.valor_variable_pct

    return {
        "terminal_id": terminal_id,
        "periodo": periodo.strftime("%Y-%m"),
        "tasa_base": (
            {
                "id": tasa_base.tarifa.id,
                "nombre": tasa_base.tarifa.nombre,
                "valor_fijo_uf": base_fijo,
                "valor_variable_pct": base_variable,
            }
            if tasa_base
            else None
        ),
        "beneficio_aplicado": (
            _format_mdr_beneficio(promo_assignment, beneficio_vigente)
            if promo_assignment
            else None
        ),
        "fijo_final_uf": fijo_final,
        "variable_final_pct": variable_final,
    }


async def _get_base_mdr_tarifa(
    session: AsyncSession,
    terminal: Terminal,
    sucursal: Sucursal,
    comercio: Comercio,
    periodo: date,
) -> Optional[MDRTarifaAsignacion]:
    """Returns the most specific active MDRTarifaAsignacion for the terminal's period."""
    for entity_type, entity_id in [
        (EntityType.SUCURSAL, terminal.sucursal_id),
        (EntityType.COMERCIO, sucursal.comercio_id),
        (EntityType.HOLDING, comercio.holding_id),
    ]:
        if entity_id is None:
            continue
        stmt = (
            select(MDRTarifaAsignacion)
            .join(MDRTarifaAsignacion.tarifa)
            .where(
                MDRTarifaAsignacion.entity_type == entity_type,
                MDRTarifaAsignacion.entity_id == entity_id,
                MDRTarifaAsignacion.fecha_inicio <= periodo,
                or_(
                    MDRTarifaAsignacion.fecha_fin.is_(None),
                    MDRTarifaAsignacion.fecha_fin >= periodo,
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
    return None


async def _get_active_mdr_promotion(
    session: AsyncSession,
    terminal: Terminal,
    sucursal: Sucursal,
    comercio: Comercio,
    periodo: date,
) -> Tuple[Optional[PromotionAssignment], Optional[EntityType]]:
    """Returns (PromotionAssignment, EntityType) for the most specific active MDR promotion."""
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
                Promotion.tipo_producto == TipoProducto.MDR,
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
            for a in assignments:
                await session.refresh(a, ["promotion"])
            non_stackable = [a for a in assignments if not a.promotion.is_stackable]
            if non_stackable:
                return max(non_stackable, key=lambda a: a.prioridad), entity_type
            return assignments[0], entity_type
    return None, None


async def _evaluate_mdr_mechanism(
    session: AsyncSession,
    promo_assignment: PromotionAssignment,
    terminal: Terminal,
    sucursal: Sucursal,
    comercio: Comercio,
    entity_type: EntityType,
    periodo: date,
) -> bool:
    """Returns is_active: bool"""
    promo = promo_assignment.promotion
    today = date.today()

    if promo.mecanismo_activacion == MecanismoActivacion.ADQUISICION:
        dias = (today - terminal.fecha_adquisicion).days
        return dias <= promo.duracion_dias

    elif promo.mecanismo_activacion == MecanismoActivacion.PERMANENTE_ILIMITADO:
        return True

    elif promo.mecanismo_activacion == MecanismoActivacion.PERMANENTE_LIMITADO:
        # For MDR, PERMANENTE_LIMITADO deactivates when volume is exceeded
        monto = await _get_monto_mes(session, entity_type, promo_assignment.entity_id, periodo)
        return monto < promo.max_volumen_mm

    elif promo.mecanismo_activacion == MecanismoActivacion.USO:
        # Active when monto_total_mm >= umbral_monto_mm
        monto = await _get_monto_mes(session, entity_type, promo_assignment.entity_id, periodo)
        return monto >= promo.umbral_monto_mm

    return False


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


def _format_mdr_beneficio(promo_assignment: PromotionAssignment, vigente: bool) -> dict:
    p = promo_assignment.promotion
    return {
        "promotion_id": p.id,
        "tipo_producto": p.tipo_producto,
        "mecanismo_activacion": p.mecanismo_activacion,
        "beneficio_mdr": p.beneficio_mdr,
        "vigente": vigente,
    }


# Re-export internal helpers so tests can import them if needed
MecanismoActivacion = MecanismoActivacion
