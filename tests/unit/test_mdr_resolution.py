from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    BeneficioMDR,
    EntityType,
    MecanismoActivacion,
    TerminalEstado,
    TipoProducto,
)
from app.models.commercial import Comercio, Holding, Sucursal, Terminal
from app.models.mdr import MDRTarifa, MDRTarifaAsignacion
from app.models.promotions import Promotion, PromotionAssignment
from app.models.transactions import TransaccionMensual
from app.services.resolucion_mdr import resolver_mdr

TODAY = date(2026, 4, 1)
PERIODO = date(2026, 4, 1)

BASE_FIJO = Decimal("0.0050")
BASE_VARIABLE = Decimal("0.0200")


async def _create_base_hierarchy(session: AsyncSession):
    holding = Holding(nombre="TestHolding", rut_holding="33.333.333-3", segmento="RETAIL")
    session.add(holding)
    await session.flush()

    comercio = Comercio(
        rut_comercio="44.444.444-4",
        nombre_fantasia="TestComercio",
        holding_id=holding.id,
    )
    session.add(comercio)
    await session.flush()

    sucursal = Sucursal(comercio_id=comercio.id, nombre="Sucursal MDR")
    session.add(sucursal)
    await session.flush()

    return holding, comercio, sucursal


async def _create_terminal(session: AsyncSession, sucursal_id: int, days_ago: int = 30) -> Terminal:
    terminal = Terminal(
        sucursal_id=sucursal_id,
        fecha_adquisicion=TODAY - timedelta(days=days_ago),
        estado=TerminalEstado.ACTIVO,
    )
    session.add(terminal)
    await session.flush()
    return terminal


async def _create_mdr_tarifa_asignacion(
    session: AsyncSession,
    entity_type: EntityType,
    entity_id: int,
    valor_fijo: Decimal = BASE_FIJO,
    valor_variable: Decimal = BASE_VARIABLE,
) -> tuple[MDRTarifa, MDRTarifaAsignacion]:
    tarifa = MDRTarifa(
        nombre="MDR Base",
        valor_fijo_uf=valor_fijo,
        valor_variable_pct=valor_variable,
        vigente_desde=date(2026, 1, 1),
        activa=True,
    )
    session.add(tarifa)
    await session.flush()

    asig = MDRTarifaAsignacion(
        tarifa_id=tarifa.id,
        entity_type=entity_type,
        entity_id=entity_id,
        fecha_inicio=date(2026, 1, 1),
        prioridad=0,
    )
    session.add(asig)
    await session.flush()
    return tarifa, asig


async def _create_mdr_promotion_assignment(
    session: AsyncSession,
    entity_type: EntityType,
    entity_id: int,
    mecanismo: MecanismoActivacion,
    beneficio_mdr: BeneficioMDR,
    valor_fijo_uf: Decimal | None = None,
    valor_variable_pct: Decimal | None = None,
    umbral_monto_mm: Decimal | None = None,
    max_volumen_mm: Decimal | None = None,
    duracion_dias: int | None = None,
) -> tuple[Promotion, PromotionAssignment]:
    promo = Promotion(
        nombre="TestMDRPromo",
        tipo_producto=TipoProducto.MDR,
        mecanismo_activacion=mecanismo,
        beneficio_mdr=beneficio_mdr,
        valor_fijo_uf=valor_fijo_uf,
        valor_variable_pct=valor_variable_pct,
        umbral_monto_mm=umbral_monto_mm,
        max_volumen_mm=max_volumen_mm,
        duracion_dias=duracion_dias,
        is_stackable=False,
        activa=True,
    )
    session.add(promo)
    await session.flush()

    asig = PromotionAssignment(
        promotion_id=promo.id,
        entity_type=entity_type,
        entity_id=entity_id,
        prioridad=0,
        activa=True,
    )
    session.add(asig)
    await session.flush()
    return promo, asig


async def _add_transaccion(
    session: AsyncSession, terminal: Terminal, sucursal_id: int, monto: Decimal
):
    trans = TransaccionMensual(
        terminal_id=terminal.id,
        sucursal_id=sucursal_id,
        periodo=PERIODO,
        monto_total_mm=monto,
        num_transacciones=100,
    )
    session.add(trans)
    await session.flush()


@pytest.mark.asyncio
async def test_mdr_uso_bajo_umbral(db_session: AsyncSession):
    """USO promo: monto=5MM, umbral=10MM → no benefit → fijo_final=base."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id)

    await _create_mdr_tarifa_asignacion(db_session, EntityType.HOLDING, holding.id)
    await _create_mdr_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.USO,
        BeneficioMDR.FIJO,
        valor_fijo_uf=Decimal("0.0010"),
        umbral_monto_mm=Decimal("10.0"),
    )
    await _add_transaccion(db_session, terminal, sucursal.id, Decimal("5.0"))

    result = await resolver_mdr(terminal.id, PERIODO, db_session)

    assert result["fijo_final_uf"] == BASE_FIJO
    assert result["beneficio_aplicado"]["vigente"] is False


@pytest.mark.asyncio
async def test_mdr_uso_sobre_umbral(db_session: AsyncSession):
    """USO promo: monto=15MM, umbral=10MM → benefit active → fijo reduced."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id)

    await _create_mdr_tarifa_asignacion(db_session, EntityType.HOLDING, holding.id)
    await _create_mdr_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.USO,
        BeneficioMDR.FIJO,
        valor_fijo_uf=Decimal("0.0010"),
        umbral_monto_mm=Decimal("10.0"),
    )
    await _add_transaccion(db_session, terminal, sucursal.id, Decimal("15.0"))

    result = await resolver_mdr(terminal.id, PERIODO, db_session)

    assert result["fijo_final_uf"] == Decimal("0.0010")
    assert result["variable_final_pct"] == BASE_VARIABLE
    assert result["beneficio_aplicado"]["vigente"] is True


@pytest.mark.asyncio
async def test_mdr_permanente_limitado_activo(db_session: AsyncSession):
    """PERMANENTE_LIMITADO: monto=35MM < max_volumen=50MM → active."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id)

    await _create_mdr_tarifa_asignacion(db_session, EntityType.HOLDING, holding.id)
    await _create_mdr_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.PERMANENTE_LIMITADO,
        BeneficioMDR.FIJO,
        valor_fijo_uf=Decimal("0.0010"),
        max_volumen_mm=Decimal("50.0"),
    )
    await _add_transaccion(db_session, terminal, sucursal.id, Decimal("35.0"))

    result = await resolver_mdr(terminal.id, PERIODO, db_session)

    assert result["fijo_final_uf"] == Decimal("0.0010")
    assert result["beneficio_aplicado"]["vigente"] is True


@pytest.mark.asyncio
async def test_mdr_permanente_limitado_excedido(db_session: AsyncSession):
    """PERMANENTE_LIMITADO: monto=62MM >= max_volumen=50MM → NOT active."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id)

    await _create_mdr_tarifa_asignacion(db_session, EntityType.HOLDING, holding.id)
    await _create_mdr_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.PERMANENTE_LIMITADO,
        BeneficioMDR.FIJO,
        valor_fijo_uf=Decimal("0.0010"),
        max_volumen_mm=Decimal("50.0"),
    )
    await _add_transaccion(db_session, terminal, sucursal.id, Decimal("62.0"))

    result = await resolver_mdr(terminal.id, PERIODO, db_session)

    assert result["fijo_final_uf"] == BASE_FIJO
    assert result["beneficio_aplicado"]["vigente"] is False


@pytest.mark.asyncio
async def test_mdr_fijo_aplica(db_session: AsyncSession):
    """beneficio_mdr=FIJO → fijo_final=promo.valor_fijo_uf, variable unchanged."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id)

    await _create_mdr_tarifa_asignacion(db_session, EntityType.HOLDING, holding.id)
    await _create_mdr_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.PERMANENTE_ILIMITADO,
        BeneficioMDR.FIJO,
        valor_fijo_uf=Decimal("0.0020"),
    )

    result = await resolver_mdr(terminal.id, PERIODO, db_session)

    assert result["fijo_final_uf"] == Decimal("0.0020")
    assert result["variable_final_pct"] == BASE_VARIABLE


@pytest.mark.asyncio
async def test_mdr_variable_aplica(db_session: AsyncSession):
    """beneficio_mdr=VARIABLE → variable_final=promo.valor_variable_pct, fijo unchanged."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id)

    await _create_mdr_tarifa_asignacion(db_session, EntityType.HOLDING, holding.id)
    await _create_mdr_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.PERMANENTE_ILIMITADO,
        BeneficioMDR.VARIABLE,
        valor_variable_pct=Decimal("0.0100"),
    )

    result = await resolver_mdr(terminal.id, PERIODO, db_session)

    assert result["fijo_final_uf"] == BASE_FIJO
    assert result["variable_final_pct"] == Decimal("0.0100")


@pytest.mark.asyncio
async def test_mdr_mixto_aplica(db_session: AsyncSession):
    """beneficio_mdr=MIXTO → both fijo and variable reduced."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id)

    await _create_mdr_tarifa_asignacion(db_session, EntityType.HOLDING, holding.id)
    await _create_mdr_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.PERMANENTE_ILIMITADO,
        BeneficioMDR.MIXTO,
        valor_fijo_uf=Decimal("0.0020"),
        valor_variable_pct=Decimal("0.0100"),
    )

    result = await resolver_mdr(terminal.id, PERIODO, db_session)

    assert result["fijo_final_uf"] == Decimal("0.0020")
    assert result["variable_final_pct"] == Decimal("0.0100")
    assert result["fijo_final_uf"] < BASE_FIJO
    assert result["variable_final_pct"] < BASE_VARIABLE
