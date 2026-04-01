from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel


class POSResolucionResponse(BaseModel):
    terminal_id: int
    periodo: str  # YYYY-MM
    tarifa_base: Optional[Dict[str, Any]] = None
    beneficio_aplicado: Optional[Dict[str, Any]] = None
    cobro_final_uf: Decimal
    ahorro_uf: Decimal
    n_terminales_beneficiadas: int


class MDRResolucionResponse(BaseModel):
    terminal_id: int
    periodo: str  # YYYY-MM
    tasa_base: Optional[Dict[str, Any]] = None
    beneficio_aplicado: Optional[Dict[str, Any]] = None
    fijo_final_uf: Optional[Decimal] = None
    variable_final_pct: Optional[Decimal] = None
