from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.core.enums import EntityType


class MDRTarifaCreate(BaseModel):
    nombre: str
    valor_fijo_uf: Optional[Decimal] = None
    valor_variable_pct: Optional[Decimal] = None
    descripcion: Optional[str] = None
    vigente_desde: date


class MDRTarifaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    valor_fijo_uf: Optional[Decimal] = None
    valor_variable_pct: Optional[Decimal] = None
    descripcion: Optional[str] = None
    vigente_desde: date
    vigente_hasta: Optional[date] = None
    activa: bool
    creado_por: Optional[int] = None
    creado_en: datetime


class MDRTarifaAsignacionCreate(BaseModel):
    tarifa_id: int
    entity_type: EntityType
    entity_id: int
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    prioridad: int = 0


class MDRTarifaAsignacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tarifa_id: int
    entity_type: EntityType
    entity_id: int
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    prioridad: int
    creado_por: Optional[int] = None
    creado_en: datetime
    tarifa: MDRTarifaResponse
