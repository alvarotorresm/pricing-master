from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.enums import EntityType


class POSTarifaCreate(BaseModel):
    nombre: str
    valor_mensual_uf: Decimal
    descripcion: Optional[str] = None
    vigente_desde: date

    @field_validator("valor_mensual_uf")
    @classmethod
    def validate_valor_mensual_uf(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00") or v > Decimal("1.00"):
            raise ValueError("valor_mensual_uf must be between 0.00 and 1.00 UF")
        return v


class POSTarifaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    valor_mensual_uf: Decimal
    descripcion: Optional[str] = None
    vigente_desde: date
    vigente_hasta: Optional[date] = None
    activa: bool
    creado_por: Optional[int] = None
    creado_en: datetime


class POSTarifaAsignacionCreate(BaseModel):
    tarifa_id: int
    entity_type: EntityType
    entity_id: int
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    prioridad: int = 0


class POSTarifaAsignacionResponse(BaseModel):
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
    tarifa: POSTarifaResponse
