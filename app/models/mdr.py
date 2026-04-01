from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Date, DateTime, Boolean, Numeric, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import EntityType


class MDRTarifa(Base):
    __tablename__ = "mdr_tarifas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    valor_fijo_uf: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    valor_variable_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(nullable=True)
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_por: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class MDRTarifaAsignacion(Base):
    __tablename__ = "mdr_tarifa_asignaciones"
    __table_args__ = (
        Index("ix_mdr_asig_entity", "entity_type", "entity_id"),
        Index("ix_mdr_asig_fechas", "fecha_inicio", "fecha_fin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tarifa_id: Mapped[int] = mapped_column(ForeignKey("mdr_tarifas.id"), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(SAEnum(EntityType, name="entity_type_mdr"), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    prioridad: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creado_por: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    tarifa: Mapped["MDRTarifa"] = relationship("MDRTarifa")
