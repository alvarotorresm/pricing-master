from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Date, DateTime, Boolean, Numeric, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import EntityType, TipoProducto, MecanismoActivacion, BeneficioPOS, BeneficioMDR


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(nullable=True)
    tipo_producto: Mapped[TipoProducto] = mapped_column(SAEnum(TipoProducto, name="tipo_producto"), nullable=False)
    mecanismo_activacion: Mapped[MecanismoActivacion] = mapped_column(SAEnum(MecanismoActivacion, name="mecanismo_activacion"), nullable=False)
    # POS benefit
    beneficio_pos: Mapped[Optional[BeneficioPOS]] = mapped_column(SAEnum(BeneficioPOS, name="beneficio_pos"), nullable=True)
    valor_cobro_uf: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    # MDR benefit
    beneficio_mdr: Mapped[Optional[BeneficioMDR]] = mapped_column(SAEnum(BeneficioMDR, name="beneficio_mdr"), nullable=True)
    valor_fijo_uf: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    valor_variable_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    # Activation params
    duracion_dias: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    umbral_monto_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    pos_por_tramo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1)
    max_pos_beneficio: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_terminales: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_volumen_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    # Meta
    is_stackable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fecha_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_por: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    assignments: Mapped[List["PromotionAssignment"]] = relationship("PromotionAssignment", back_populates="promotion")


class PromotionAssignment(Base):
    __tablename__ = "promotion_assignments"
    __table_args__ = (
        Index("ix_promo_asig_entity", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(ForeignKey("promotions.id"), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(SAEnum(EntityType, name="entity_type_promo"), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    prioridad: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    creado_por: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    promotion: Mapped["Promotion"] = relationship("Promotion", back_populates="assignments")
