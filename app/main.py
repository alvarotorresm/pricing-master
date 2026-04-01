from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import commercial, mdr_tarifas, pos_tarifas, promotions, resolucion


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="PricingMaster API",
    description="B2B pricing management for payment acquirers in Chile",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(commercial.router)
app.include_router(pos_tarifas.router)
app.include_router(mdr_tarifas.router)
app.include_router(promotions.router)
app.include_router(resolucion.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
