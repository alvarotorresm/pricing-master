from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    BeneficioPOS,
    EntityType,
    MecanismoActivacion,
    TerminalEstado,
    TipoProducto,
)
from app.models.commercial import Comercio, Holding, Sucursal, Terminal
from app.models.pos import POSTarifa, POSTarifaAsignacion
from app.models.promotions import Promotion, PromotionAssignment
from app.models.transactions import TransaccionMensual
from app.services.resolucion_pos import resolver_pos

TODAY = date(2026, 4, 1)  # fixed reference matching project context
PERIODO = date(2026, 4, 1)  # first day of April 2026


async def _create_base_hierarchy(session: AsyncSession):
    """Helper: creates holding → comercio → sucursal and returns them."""
    holding = Holding(nombre="TestHolding", rut_holding="11.111.111-1", segmento="RETAIL")
    session.add(holding)
    await session.flush()

    comercio = Comercio(
        rut_comercio="22.222.222-2",
        nombre_fantasia="TestComercio",
        holding_id=holding.id,
    )
    session.add(comercio)
    await session.flush()

    sucursal = Sucursal(comercio_id=comercio.id, nombre="Sucursal Central")
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


async def _create_pos_tarifa_asignacion(
    session: AsyncSession,
    valor: Decimal,
    entity_type: EntityType,
    entity_id: int,
    prioridad: int = 0,
) -> tuple[POSTarifa, POSTarifaAsignacion]:
    tarifa = POSTarifa(
        nombre=f"Tarifa {valor} UF",
        valor_mensual_uf=valor,
        vigente_desde=date(2026, 1, 1),
        activa=True,
    )
    session.add(tarifa)
    await session.flush()

    asig = POSTarifaAsignacion(
        tarifa_id=tarifa.id,
        entity_type=entity_type,
        entity_id=entity_id,
        fecha_inicio=date(2026, 1, 1),
        prioridad=prioridad,
    )
    session.add(asig)
    await session.flush()
    return tarifa, asig


async def _create_promotion_assignment(
    session: AsyncSession,
    entity_type: EntityType,
    entity_id: int,
    mecanismo: MecanismoActivacion,
    beneficio_pos: BeneficioPOS,
    valor_cobro_uf: Decimal | None = None,
    duracion_dias: int | None = None,
    umbral_monto_mm: Decimal | None = None,
    pos_por_tramo: int | None = None,
    max_pos_beneficio: int | None = None,
    max_terminales: int | None = None,
    prioridad: int = 0,
) -> tuple[Promotion, PromotionAssignment]:
    promo = Promotion(
        nombre="TestPromo",
        tipo_producto=TipoProducto.POS,
        mecanismo_activacion=mecanismo,
        beneficio_pos=beneficio_pos,
        valor_cobro_uf=valor_cobro_uf,
        duracion_dias=duracion_dias,
        umbral_monto_mm=umbral_monto_mm,
        pos_por_tramo=pos_por_tramo,
        max_pos_beneficio=max_pos_beneficio,
        max_terminales=max_terminales,
        is_stackable=False,
        activa=True,
    )
    session.add(promo)
    await session.flush()

    asig = PromotionAssignment(
        promotion_id=promo.id,
        entity_type=entity_type,
        entity_id=entity_id,
        prioridad=prioridad,
        activa=True,
    )
    session.add(asig)
    await session.flush()
    return promo, asig


@pytest.mark.asyncio
async def test_pos_adquisicion_dentro_plazo(db_session: AsyncSession):
    """ADQUISICION promo within window → cobro = 0.00 (COSTO_CERO)."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id, days_ago=30)

    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.65"), EntityType.HOLDING, holding.id
    )
    await _create_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.ADQUISICION,
        BeneficioPOS.COSTO_CERO,
        duracion_dias=90,
    )

    result = await resolver_pos(terminal.id, PERIODO, db_session)

    assert result["cobro_final_uf"] == Decimal("0.00")
    assert result["beneficio_aplicado"] is not None
    assert result["beneficio_aplicado"]["vigente"] is True


@pytest.mark.asyncio
async def test_pos_adquisicion_fuera_plazo(db_session: AsyncSession):
    """ADQUISICION promo outside window → cobro = base tarifa."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id, days_ago=120)

    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.65"), EntityType.HOLDING, holding.id
    )
    await _create_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.ADQUISICION,
        BeneficioPOS.COSTO_CERO,
        duracion_dias=90,
    )

    result = await resolver_pos(terminal.id, PERIODO, db_session)

    assert result["cobro_final_uf"] == Decimal("0.65")
    assert result["beneficio_aplicado"]["vigente"] is False


@pytest.mark.asyncio
async def test_pos_uso_tramos_0_terminales(db_session: AsyncSession):
    """USO promo: monto=5MM, umbral=8MM → 0 tramos → no benefit."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id, days_ago=30)

    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.65"), EntityType.HOLDING, holding.id
    )
    await _create_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.USO,
        BeneficioPOS.COSTO_CERO,
        umbral_monto_mm=Decimal("8.0"),
        pos_por_tramo=1,
    )

    trans = TransaccionMensual(
        terminal_id=terminal.id,
        sucursal_id=sucursal.id,
        periodo=PERIODO,
        monto_total_mm=Decimal("5.0"),
        num_transacciones=50,
    )
    db_session.add(trans)
    await db_session.flush()

    result = await resolver_pos(terminal.id, PERIODO, db_session)

    assert result["cobro_final_uf"] == Decimal("0.65")


@pytest.mark.asyncio
async def test_pos_uso_tramos_1_terminal(db_session: AsyncSession):
    """USO promo: monto=8MM, umbral=8MM → 1 tramo, pos_por_tramo=1 → oldest terminal free."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    # Create 2 terminals; oldest should get benefit
    terminal_old = await _create_terminal(db_session, sucursal.id, days_ago=60)
    terminal_new = await _create_terminal(db_session, sucursal.id, days_ago=10)

    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.65"), EntityType.HOLDING, holding.id
    )
    await _create_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.USO,
        BeneficioPOS.COSTO_CERO,
        umbral_monto_mm=Decimal("8.0"),
        pos_por_tramo=1,
    )

    for t in [terminal_old, terminal_new]:
        trans = TransaccionMensual(
            terminal_id=t.id,
            sucursal_id=sucursal.id,
            periodo=PERIODO,
            monto_total_mm=Decimal("4.0"),  # total = 8.0 for holding
            num_transacciones=40,
        )
        db_session.add(trans)
    await db_session.flush()

    result_old = await resolver_pos(terminal_old.id, PERIODO, db_session)
    result_new = await resolver_pos(terminal_new.id, PERIODO, db_session)

    assert result_old["cobro_final_uf"] == Decimal("0.00"), "Oldest terminal should be free"
    assert result_new["cobro_final_uf"] == Decimal("0.65"), "Newer terminal should pay base"


@pytest.mark.asyncio
async def test_pos_uso_cap_3_terminals(db_session: AsyncSession):
    """USO promo: monto=40MM, umbral=8MM → 5 tramos, pos_por_tramo=1 → min(5,3)=3 → all free."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminals = [await _create_terminal(db_session, sucursal.id, days_ago=60 - i * 5) for i in range(3)]

    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.65"), EntityType.HOLDING, holding.id
    )
    await _create_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.USO,
        BeneficioPOS.COSTO_CERO,
        umbral_monto_mm=Decimal("8.0"),
        pos_por_tramo=1,
    )

    # Total monto = 40MM across terminals
    for i, t in enumerate(terminals):
        trans = TransaccionMensual(
            terminal_id=t.id,
            sucursal_id=sucursal.id,
            periodo=PERIODO,
            monto_total_mm=Decimal("13.34") if i < 2 else Decimal("13.32"),
            num_transacciones=100,
        )
        db_session.add(trans)
    await db_session.flush()

    for t in terminals:
        result = await resolver_pos(t.id, PERIODO, db_session)
        assert result["cobro_final_uf"] == Decimal("0.00"), f"Terminal {t.id} should be free"


@pytest.mark.asyncio
async def test_pos_permanente_limitado_activo(db_session: AsyncSession):
    """PERMANENTE_LIMITADO: 3 active terminals, max=5 → benefit active → cobro=0.00."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminals = [await _create_terminal(db_session, sucursal.id, days_ago=30 + i) for i in range(3)]

    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.65"), EntityType.HOLDING, holding.id
    )
    await _create_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.PERMANENTE_LIMITADO,
        BeneficioPOS.COSTO_CERO,
        max_terminales=5,
    )

    result = await resolver_pos(terminals[0].id, PERIODO, db_session)
    assert result["cobro_final_uf"] == Decimal("0.00")


@pytest.mark.asyncio
async def test_pos_permanente_limitado_inactivo(db_session: AsyncSession):
    """PERMANENTE_LIMITADO: 6 active terminals, max=5 → benefit NOT active → cobro=base."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminals = [await _create_terminal(db_session, sucursal.id, days_ago=30 + i) for i in range(6)]

    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.65"), EntityType.HOLDING, holding.id
    )
    await _create_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.PERMANENTE_LIMITADO,
        BeneficioPOS.COSTO_CERO,
        max_terminales=5,
    )

    result = await resolver_pos(terminals[0].id, PERIODO, db_session)
    assert result["cobro_final_uf"] == Decimal("0.65")


@pytest.mark.asyncio
async def test_pos_permanente_ilimitado(db_session: AsyncSession):
    """PERMANENTE_ILIMITADO: always active regardless of terminal count."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id, days_ago=30)

    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.65"), EntityType.HOLDING, holding.id
    )
    await _create_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.PERMANENTE_ILIMITADO,
        BeneficioPOS.COSTO_CERO,
    )

    result = await resolver_pos(terminal.id, PERIODO, db_session)
    assert result["cobro_final_uf"] == Decimal("0.00")


@pytest.mark.asyncio
async def test_pos_hierarchy_sucursal_overrides_comercio(db_session: AsyncSession):
    """SUCURSAL tariff (0.45) overrides COMERCIO tariff (0.89)."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id, days_ago=30)

    # COMERCIO-level tariff
    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.89"), EntityType.COMERCIO, comercio.id
    )
    # SUCURSAL-level tariff (more specific, should win)
    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.45"), EntityType.SUCURSAL, sucursal.id
    )

    result = await resolver_pos(terminal.id, PERIODO, db_session)

    assert result["cobro_final_uf"] == Decimal("0.45")
    assert result["tarifa_base"]["valor_mensual_uf"] == Decimal("0.45")


@pytest.mark.asyncio
async def test_pos_precio_rebajado(db_session: AsyncSession):
    """PRECIO_REBAJADO with valor_cobro_uf=0.20, base=0.65 → cobro=0.20, ahorro=0.45."""
    holding, comercio, sucursal = await _create_base_hierarchy(db_session)
    terminal = await _create_terminal(db_session, sucursal.id, days_ago=30)

    await _create_pos_tarifa_asignacion(
        db_session, Decimal("0.65"), EntityType.HOLDING, holding.id
    )
    await _create_promotion_assignment(
        db_session,
        EntityType.HOLDING,
        holding.id,
        MecanismoActivacion.PERMANENTE_ILIMITADO,
        BeneficioPOS.PRECIO_REBAJADO,
        valor_cobro_uf=Decimal("0.20"),
    )

    result = await resolver_pos(terminal.id, PERIODO, db_session)

    assert result["cobro_final_uf"] == Decimal("0.20")
    assert result["ahorro_uf"] == Decimal("0.45")
