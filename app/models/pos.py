from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Date, DateTime, Boolean, Numeric, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import EntityType


class POSTarifa(Base):
    __tablename__ = "pos_tarifas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    valor_mensual_uf: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(nullable=True)
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_por: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # FK to users in v2
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class POSTarifaAsignacion(Base):
    __tablename__ = "pos_tarifa_asignaciones"
    __table_args__ = (
        Index("ix_pos_asig_entity", "entity_type", "entity_id"),
        Index("ix_pos_asig_fechas", "fecha_inicio", "fecha_fin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tarifa_id: Mapped[int] = mapped_column(ForeignKey("pos_tarifas.id"), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(SAEnum(EntityType, name="entity_type_pos"), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    prioridad: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creado_por: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    tarifa: Mapped["POSTarifa"] = relationship("POSTarifa")
