from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.core.enums import (
    BeneficioMDR,
    BeneficioPOS,
    EntityType,
    MecanismoActivacion,
    TipoProducto,
)


class PromotionCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo_producto: TipoProducto
    mecanismo_activacion: MecanismoActivacion
    # POS benefit fields
    beneficio_pos: Optional[BeneficioPOS] = None
    valor_cobro_uf: Optional[Decimal] = None
    # MDR benefit fields
    beneficio_mdr: Optional[BeneficioMDR] = None
    valor_fijo_uf: Optional[Decimal] = None
    valor_variable_pct: Optional[Decimal] = None
    # Activation params
    duracion_dias: Optional[int] = None
    umbral_monto_mm: Optional[Decimal] = None
    pos_por_tramo: Optional[int] = None
    max_pos_beneficio: Optional[int] = None
    max_terminales: Optional[int] = None
    max_volumen_mm: Optional[Decimal] = None
    # Meta
    is_stackable: bool = False
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    activa: bool = True


class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: Optional[str] = None
    tipo_producto: TipoProducto
    mecanismo_activacion: MecanismoActivacion
    beneficio_pos: Optional[BeneficioPOS] = None
    valor_cobro_uf: Optional[Decimal] = None
    beneficio_mdr: Optional[BeneficioMDR] = None
    valor_fijo_uf: Optional[Decimal] = None
    valor_variable_pct: Optional[Decimal] = None
    duracion_dias: Optional[int] = None
    umbral_monto_mm: Optional[Decimal] = None
    pos_por_tramo: Optional[int] = None
    max_pos_beneficio: Optional[int] = None
    max_terminales: Optional[int] = None
    max_volumen_mm: Optional[Decimal] = None
    is_stackable: bool
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    activa: bool
    creado_por: Optional[int] = None
    creado_en: datetime


class PromotionAssignmentCreate(BaseModel):
    promotion_id: int
    entity_type: EntityType
    entity_id: int
    prioridad: int = 0
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class PromotionAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    promotion_id: int
    entity_type: EntityType
    entity_id: int
    prioridad: int
    activa: bool
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    creado_por: Optional[int] = None
    creado_en: datetime
    promotion: PromotionResponse
