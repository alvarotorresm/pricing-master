from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.core.enums import TerminalEstado


class HoldingCreate(BaseModel):
    nombre: str
    rut_holding: str
    segmento: Optional[str] = None


class HoldingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    rut_holding: str
    segmento: Optional[str] = None


class ComercioCreate(BaseModel):
    rut_comercio: str
    nombre_fantasia: str
    holding_id: Optional[int] = None
    external_id: Optional[str] = None
    mcc: Optional[str] = None


class ComercioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rut_comercio: str
    nombre_fantasia: str
    holding_id: Optional[int] = None
    external_id: Optional[str] = None
    mcc: Optional[str] = None


class SucursalCreate(BaseModel):
    comercio_id: int
    nombre: str
    direccion: Optional[str] = None


class SucursalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comercio_id: int
    nombre: str
    direccion: Optional[str] = None


class TerminalCreate(BaseModel):
    sucursal_id: int
    external_terminal_id: Optional[str] = None
    fecha_adquisicion: date
    estado: TerminalEstado = TerminalEstado.ACTIVO


class TerminalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sucursal_id: int
    external_terminal_id: Optional[str] = None
    fecha_adquisicion: date
    estado: TerminalEstado


class TerminalUpdate(BaseModel):
    estado: TerminalEstado
