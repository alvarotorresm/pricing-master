from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BeneficioMDR, BeneficioPOS, MecanismoActivacion, TipoProducto
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.promotions import Promotion, PromotionAssignment
from app.schemas.promotions import PromotionAssignmentCreate, PromotionCreate


async def get_promotions(
    session: AsyncSession,
    tipo_producto: Optional[TipoProducto] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Promotion]:
    stmt = select(Promotion).where(Promotion.activa == True)
    if tipo_producto is not None:
        stmt = stmt.where(Promotion.tipo_producto == tipo_producto)
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_promotion(session: AsyncSession, data: PromotionCreate) -> Promotion:
    # Validate POS-specific business rules
    if data.tipo_producto == TipoProducto.POS:
        if data.beneficio_pos == BeneficioPOS.PRECIO_REBAJADO:
            if data.valor_cobro_uf is None:
                raise BusinessRuleError(
                    "valor_cobro_uf is required for PRECIO_REBAJADO benefit"
                )
        if data.mecanismo_activacion == MecanismoActivacion.USO:
            if not data.umbral_monto_mm or data.umbral_monto_mm <= 0:
                raise BusinessRuleError(
                    "umbral_monto_mm > 0 is required for USO mechanism"
                )
            if data.pos_por_tramo is None or data.pos_por_tramo < 1:
                raise BusinessRuleError(
                    "pos_por_tramo >= 1 is required for POS USO mechanism"
                )
        if data.mecanismo_activacion == MecanismoActivacion.PERMANENTE_LIMITADO:
            if data.max_terminales is None:
                raise BusinessRuleError(
                    "max_terminales is required for PERMANENTE_LIMITADO mechanism"
                )
        if data.mecanismo_activacion == MecanismoActivacion.ADQUISICION:
            if data.duracion_dias is None:
                raise BusinessRuleError(
                    "duracion_dias is required for ADQUISICION mechanism"
                )

    # Validate MDR-specific business rules
    if data.tipo_producto == TipoProducto.MDR:
        if data.beneficio_mdr in (BeneficioMDR.FIJO, BeneficioMDR.MIXTO):
            if data.valor_fijo_uf is None:
                raise BusinessRuleError(
                    "valor_fijo_uf is required for FIJO or MIXTO MDR benefit"
                )
        if data.beneficio_mdr in (BeneficioMDR.VARIABLE, BeneficioMDR.MIXTO):
            if data.valor_variable_pct is None:
                raise BusinessRuleError(
                    "valor_variable_pct is required for VARIABLE or MIXTO MDR benefit"
                )
        if data.mecanismo_activacion == MecanismoActivacion.USO:
            if not data.umbral_monto_mm or data.umbral_monto_mm <= 0:
                raise BusinessRuleError(
                    "umbral_monto_mm > 0 is required for USO mechanism"
                )
        if data.mecanismo_activacion == MecanismoActivacion.PERMANENTE_LIMITADO:
            if data.max_volumen_mm is None:
                raise BusinessRuleError(
                    "max_volumen_mm is required for PERMANENTE_LIMITADO MDR mechanism"
                )
        if data.mecanismo_activacion == MecanismoActivacion.ADQUISICION:
            if data.duracion_dias is None:
                raise BusinessRuleError(
                    "duracion_dias is required for ADQUISICION mechanism"
                )

    promotion = Promotion(
        nombre=data.nombre,
        descripcion=data.descripcion,
        tipo_producto=data.tipo_producto,
        mecanismo_activacion=data.mecanismo_activacion,
        beneficio_pos=data.beneficio_pos,
        valor_cobro_uf=data.valor_cobro_uf,
        beneficio_mdr=data.beneficio_mdr,
        valor_fijo_uf=data.valor_fijo_uf,
        valor_variable_pct=data.valor_variable_pct,
        duracion_dias=data.duracion_dias,
        umbral_monto_mm=data.umbral_monto_mm,
        pos_por_tramo=data.pos_por_tramo,
        max_pos_beneficio=data.max_pos_beneficio,
        max_terminales=data.max_terminales,
        max_volumen_mm=data.max_volumen_mm,
        is_stackable=data.is_stackable,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        activa=data.activa,
    )
    session.add(promotion)
    await session.flush()
    await session.refresh(promotion)
    return promotion


async def create_promotion_assignment(
    session: AsyncSession, data: PromotionAssignmentCreate
) -> PromotionAssignment:
    promotion = await session.get(Promotion, data.promotion_id)
    if not promotion:
        raise NotFoundError(f"Promotion {data.promotion_id} not found")
    asig = PromotionAssignment(
        promotion_id=data.promotion_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        prioridad=data.prioridad,
        activa=True,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
    )
    session.add(asig)
    await session.flush()
    await session.refresh(asig, ["promotion"])
    return asig


async def get_promotion_assignments(
    session: AsyncSession, entity_type: str, entity_id: int
) -> List[PromotionAssignment]:
    today = date.today()
    stmt = (
        select(PromotionAssignment)
        .where(
            PromotionAssignment.entity_type == entity_type,
            PromotionAssignment.entity_id == entity_id,
            PromotionAssignment.activa == True,
            or_(
                PromotionAssignment.fecha_inicio.is_(None),
                PromotionAssignment.fecha_inicio <= today,
            ),
            or_(
                PromotionAssignment.fecha_fin.is_(None),
                PromotionAssignment.fecha_fin >= today,
            ),
        )
        .order_by(PromotionAssignment.prioridad.desc())
    )
    result = await session.execute(stmt)
    assignments = list(result.scalars().all())
    for a in assignments:
        await session.refresh(a, ["promotion"])
    return assignments


async def deactivate_promotion_assignment(
    session: AsyncSession, asig_id: int
) -> None:
    asig = await session.get(PromotionAssignment, asig_id)
    if not asig:
        raise NotFoundError(f"PromotionAssignment {asig_id} not found")
    asig.activa = False
    asig.fecha_fin = date.today()
    await session.flush()
