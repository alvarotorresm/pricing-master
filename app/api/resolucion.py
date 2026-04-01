from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.resolucion import MDRResolucionResponse, POSResolucionResponse
from app.services.resolucion_mdr import resolver_mdr
from app.services.resolucion_pos import resolver_pos

router = APIRouter(prefix="/api", tags=["Resolucion"])


def _parse_periodo(periodo: str) -> date:
    """Parse a 'YYYY-MM' string into a date set to the first of that month."""
    try:
        year, month = periodo.split("-")
        return date(int(year), int(month), 1)
    except (ValueError, AttributeError):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="periodo must be in YYYY-MM format (e.g. '2026-02')",
        )


@router.get("/pos-resolucion", response_model=POSResolucionResponse)
async def resolver_pos_endpoint(
    terminal_id: int = Query(..., description="Terminal ID"),
    periodo: str = Query(..., description="Billing period in YYYY-MM format"),
    session: AsyncSession = Depends(get_db),
) -> POSResolucionResponse:
    periodo_date = _parse_periodo(periodo)
    result = await resolver_pos(terminal_id, periodo_date, session)
    return POSResolucionResponse(**result)


@router.get("/mdr-resolucion", response_model=MDRResolucionResponse)
async def resolver_mdr_endpoint(
    terminal_id: int = Query(..., description="Terminal ID"),
    periodo: str = Query(..., description="Billing period in YYYY-MM format"),
    session: AsyncSession = Depends(get_db),
) -> MDRResolucionResponse:
    periodo_date = _parse_periodo(periodo)
    result = await resolver_mdr(terminal_id, periodo_date, session)
    return MDRResolucionResponse(**result)
