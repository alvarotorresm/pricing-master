# CLAUDE.md — PricingMaster

This file provides context and guidance for AI assistants working on this repository.

---

## Project Overview

**PricingMaster** is a B2B pricing management system for payment acquirers in the Chilean market. It centralizes the configuration of two pricing components for merchants:

1. **POS Tariffs** — Fixed monthly terminal rental fees (in UF, Chilean Unidad de Fomento)
2. **MDR (Merchant Discount Rate)** — Transaction processing fees composed of a fixed UF component and a variable percentage component

The system supports hierarchical pricing (Holding → Merchant → Branch), promotion/benefit management, and a resolution engine that determines the final charge per terminal per period.

**Current state:** v1 scaffold implemented. Full FastAPI + PostgreSQL application with all 11 database models, Pydantic schemas, POS + MDR resolution engines, REST API routes, unit tests, and Docker setup. No authentication in v1 (all routes public — JWT + RBAC planned for v2).

---

## Repository Structure

```
pricing-master/
├── app/
│   ├── main.py                        # FastAPI entry point
│   ├── config.py                      # Pydantic BaseSettings
│   ├── dependencies.py                # DB session injection
│   ├── core/
│   │   ├── enums.py                   # All domain ENUMs
│   │   └── exceptions.py             # HTTP exception wrappers
│   ├── db/
│   │   ├── base.py                    # SQLAlchemy DeclarativeBase
│   │   └── session.py                # Async engine + session factory
│   ├── models/                        # SQLAlchemy 2.x models (11 tables)
│   │   ├── commercial.py             # Holdings, Comercios, Sucursales, Terminales
│   │   ├── pos.py                    # POS_Tarifas, POS_Tarifa_Asignaciones
│   │   ├── mdr.py                    # MDR_Tarifas, MDR_Tarifa_Asignaciones
│   │   ├── promotions.py             # Promotions, Promotion_Assignments
│   │   └── transactions.py           # Transacciones_Mensual
│   ├── schemas/                       # Pydantic v2 schemas
│   │   ├── commercial.py
│   │   ├── pos.py
│   │   ├── mdr.py
│   │   ├── promotions.py
│   │   └── resolucion.py
│   ├── services/
│   │   ├── pos_service.py
│   │   ├── mdr_service.py
│   │   ├── promotion_service.py
│   │   ├── resolucion_pos.py         # ⚡ POS resolution engine
│   │   └── resolucion_mdr.py         # ⚡ MDR resolution engine
│   └── api/
│       ├── commercial.py
│       ├── pos_tarifas.py
│       ├── mdr_tarifas.py
│       ├── promotions.py
│       └── resolucion.py
├── alembic/                           # DB migrations
│   └── versions/
├── tests/
│   ├── conftest.py                   # Async SQLite in-memory fixtures
│   ├── unit/
│   │   ├── test_pos_resolution.py
│   │   ├── test_mdr_resolution.py
│   │   └── test_validations.py
│   └── integration/
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── TASKS.md
├── CLAUDE.md
└── README.md
```

The main specification document (`# Proyecto PricingMaster.md`) is the authoritative source of truth for all business logic, data models, API design, and validation rules.

---

## Implementation Status

| Component | Status | Notes |
|---|---|---|
| Database models | ✅ v1 | All 11 tables, SQLAlchemy 2.x Mapped[] syntax |
| Pydantic schemas | ✅ v1 | Pydantic v2, from_attributes=True |
| POS resolution engine | ✅ v1 | ADQUISICION, USO tranches, PERMANENTE_LIMITADO/ILIMITADO |
| MDR resolution engine | ✅ v1 | All mecanismos, FIJO/VARIABLE/MIXTO |
| REST API | ✅ v1 | All 20+ endpoints, no auth |
| Alembic migrations | ✅ v1 | Async env.py, autogenerate ready |
| Docker setup | ✅ v1 | PostgreSQL 16 + FastAPI |
| Unit tests | ✅ v1 | Resolution engine + validations |
| Authentication (JWT) | 🔲 v2 | Planned: operador/supervisor/admin roles |
| Approval workflow | 🔲 v2 | MDR rate reductions requiring supervisor |
| Audit logs | 🔲 v3 | Full MDR change history |
| Frontend | 🔲 v4 | React + TypeScript dashboard |

---

## Domain Model

### Entity Hierarchy

```
Holdings (corporate groups)
  └── Comercios (individual merchants, holding_id nullable)
        └── Sucursales (physical branch locations)
              └── Terminales (POS terminals, fecha_adquisicion tracked)
```

- A `Comercio` can exist without a `Holding` (independent merchant)
- A `Sucursal` must belong to exactly one `Comercio`
- A `Terminal` must belong to exactly one `Sucursal`
- Pricing precedence: **SUCURSAL > COMERCIO > HOLDING** (most specific wins)

### Database Tables (11 total)

| Table | Purpose |
|---|---|
| `Holdings` | Corporate groups (id, nombre, rut_holding, segmento) |
| `Comercios` | Individual merchants (id, rut_comercio, nombre_fantasia, holding_id FK nullable, external_id, mcc) |
| `Sucursales` | Branch locations (id, comercio_id FK, nombre, direccion) |
| `Terminales` | POS terminals (id, sucursal_id FK, external_terminal_id, fecha_adquisicion, estado ENUM) |
| `POS_Tarifas` | Base POS tariff catalog — range 0.00–1.00 UF, Decimal(4,2), never deleted |
| `POS_Tarifa_Asignaciones` | Maps base POS tariff to holding/merchant/branch |
| `MDR_Tarifas` | Base MDR rate catalog — fijo Decimal(10,4) + variable Decimal(6,4), never deleted |
| `MDR_Tarifa_Asignaciones` | Maps base MDR rate to holding/merchant/branch |
| `Promotions` | Benefits catalog (POS or MDR, activation mechanism, benefit type) |
| `Promotion_Assignments` | Maps a promotion to a holding/merchant/branch |
| `Transacciones_Mensual` | Monthly transaction aggregates per terminal (for usage-based activation) |

### Key ENUMs

- `Terminal.estado`: `ACTIVO`, `INACTIVO`, `BAJA`
- `entity_type` (used across assignment tables): `HOLDING`, `COMERCIO`, `SUCURSAL`
- `Promotions.tipo_producto`: `POS`, `MDR`
- `Promotions.mecanismo_activacion`: `ADQUISICION`, `USO`, `PERMANENTE_LIMITADO`, `PERMANENTE_ILIMITADO`
- `Promotions.beneficio_pos`: `COSTO_CERO`, `PRECIO_REBAJADO`
- `Promotions.beneficio_mdr`: `FIJO`, `VARIABLE`, `MIXTO`

---

## Core Business Logic

### POS Resolution Engine

**Input:** `terminal_id`, `periodo` (month/year)

**Step 1 — Get base POS tariff** (SUCURSAL > COMERCIO > HOLDING precedence):
- Query `POS_Tarifa_Asignaciones` where `fecha_inicio <= periodo <= fecha_fin`
- Use most specific level match; fall back to system default if none

**Step 2 — Evaluate POS promotion** (same SUCURSAL > COMERCIO > HOLDING hierarchy):

| Mechanism | Active when |
|---|---|
| `ADQUISICION` | `(today − terminal.fecha_adquisicion) <= promo.duracion_dias` |
| `USO` | `tramos = floor(monto_mes / umbral_monto_mm)`; terminal gets benefit if its rank (by `fecha_adquisicion ASC`) ≤ `min(tramos × pos_por_tramo, max_pos_beneficio ?? total_active_terminals)` |
| `PERMANENTE_LIMITADO` | `count(ACTIVO terminals in scope) <= promo.max_terminales` |
| `PERMANENTE_ILIMITADO` | Always active |

**Step 3 — Calculate final charge:**
- No benefit → `cobro = tarifa_base.valor_mensual_uf`
- `COSTO_CERO` → `cobro = 0.00 UF`
- `PRECIO_REBAJADO` → `cobro = promo.valor_cobro_uf`

**Output:** `{ cobro_final_uf, tarifa_base_uf, beneficio_aplicado, n_terminales_beneficiadas, ahorro_uf }`

### MDR Resolution Engine

**Input:** `terminal_id`, `periodo`

**Step 1 — Get base MDR rate** (same SUCURSAL > COMERCIO > HOLDING precedence)

**Step 2 — Evaluate MDR promotion:**

| Mechanism | Active when |
|---|---|
| `ADQUISICION` | `(today − terminal.fecha_adquisicion) <= promo.duracion_dias` |
| `USO` | `Transacciones_Mensual.monto_total_mm >= promo.umbral_monto_mm` |
| `PERMANENTE_LIMITADO` | `monto_total_mm < promo.max_volumen_mm` (deactivates when volume exceeded) |
| `PERMANENTE_ILIMITADO` | Always active |

**Step 3 — Calculate final MDR rates** based on `beneficio_mdr`:
- `FIJO` → reduced `valor_fijo_uf`, unchanged `valor_variable_pct`
- `VARIABLE` → unchanged `valor_fijo_uf`, reduced `valor_variable_pct`
- `MIXTO` → both components reduced

**Output:** `{ fijo_final_uf, variable_final_pct, tasa_base, beneficio_aplicado }`

### Conflict Resolution Between Promotions

1. Hierarchy wins: SUCURSAL promotions suppress COMERCIO and HOLDING promotions
2. Within the same level: if any promotion has `is_stackable=false`, only the one with the highest `prioridad` applies; if all have `is_stackable=true`, they all apply

---

## API Endpoints

All endpoints are prefixed with `/api`.

### POS Tariffs
```
GET    /pos-tarifas                                      List base POS tariff catalog
POST   /pos-tarifas                                      Create new base POS tariff
GET    /pos-tarifas/:id                                  Get tariff details
PUT    /pos-tarifas/:id                                  Update (creates new catalog version)
POST   /pos-tarifa-asignaciones                          Assign POS tariff to entity
GET    /pos-tarifa-asignaciones?entity_type=&entity_id=  Get entity's active POS tariff
DELETE /pos-tarifa-asignaciones/:id                      Deactivate assignment (sets fecha_fin)
```

### MDR Tariffs
```
GET    /mdr-tarifas                                      List base MDR rate catalog
POST   /mdr-tarifas                                      Create new base MDR rate
GET    /mdr-tarifas/:id                                  Get rate details
PUT    /mdr-tarifas/:id                                  Update (creates new catalog version)
POST   /mdr-tarifa-asignaciones                          Assign MDR rate to entity
GET    /mdr-tarifa-asignaciones?entity_type=&entity_id=  Get entity's active MDR rate
DELETE /mdr-tarifa-asignaciones/:id                      Deactivate assignment (sets fecha_fin)
```

### Promotions / Benefits
```
GET    /promotions                                       List benefits catalog (filter by tipo_producto)
POST   /promotions                                       Create new POS or MDR benefit
POST   /promotion-assignments                            Assign benefit to entity
GET    /promotion-assignments?entity_type=&entity_id=   Get entity's active benefits
DELETE /promotion-assignments/:id                        Deactivate benefit assignment
```

### Resolution Engine
```
GET    /pos-resolucion?terminal_id=&periodo=2026-02      Resolve final POS charge for terminal
GET    /mdr-resolucion?terminal_id=&periodo=2026-02      Resolve final MDR rates for terminal
```

Resolution endpoints must respond in **< 200ms** (non-functional requirement — cannot block POS transactions).

---

## Business Validation Rules

| Rule | Description |
|---|---|
| `PRECIO_REBAJADO < BASE` | POS benefit value must be strictly less than the current base tariff |
| `POS tariff range` | `POS_Tarifas.valor_mensual_uf` must be 0.00–1.00 UF (2 decimal places) |
| `MDR FIJO benefit < base` | If `beneficio_mdr` is `FIJO` or `MIXTO`, `valor_fijo_uf` must be < base |
| `MDR VARIABLE benefit < base` | If `beneficio_mdr` is `VARIABLE` or `MIXTO`, `valor_variable_pct` must be < base |
| `USO: pos_por_tramo >= 1` | Required when `mecanismo_activacion=USO` and `tipo_producto=POS`; `umbral_monto_mm > 0` |
| `One active base tariff` | An entity cannot have two simultaneous active base tariff assignments for the same period (POS and MDR checked independently) |
| **Soft delete only** | Tariffs and promotions are **never deleted** — marked `activa=false` or given a `fecha_fin` |
| **Versioning** | Changes to `POS_Tarifas` or `MDR_Tarifas` values create a **new record**; the previous record is never modified |

---

## Non-Functional Requirements

- **Performance:** Resolution engine must respond in < 200ms
- **Security:** RBAC — separate roles for creating vs. approving promotions
- **MDR Audit:** MDR changes touching money/settlements require:
  - Promotion versioning (never delete, only deactivate)
  - User action logs (who approved what and when)
  - Approval workflow for significant rate reductions (e.g., dropping to 0%) requiring a "Supervisión" role
- **Decimal precision:**
  - POS: 2 decimal places (`Decimal(4,2)`)
  - MDR fixed: 4 decimal places (`Decimal(10,4)`)
  - MDR variable: 4 decimal places (`Decimal(6,4)`)

---

## Onboarding Flow

1. Merchant is created in the system
2. System detects by RUT or name whether it belongs to an existing Holding
3. If the Holding has an active base tariff and/or "welcome" promotion, the new merchant **automatically inherits** them — no manual intervention needed

---

## Development Guidelines (for when implementation begins)

### Architecture Recommendations
- The resolution engines (POS + MDR) are the performance-critical paths — optimize queries with indexes on `entity_type`, `entity_id`, `fecha_inicio`, `fecha_fin`, and `activa`
- Use database transactions for assignment operations to prevent partial states
- Implement the approval workflow for MDR changes before exposing admin endpoints

### Conventions to Follow
- **No hard deletes** — always use soft delete (`activa=false`) or date-based deactivation (`fecha_fin = today`)
- **No in-place updates** to tariff catalog values — always create a new record and set `vigente_hasta` on the old one
- All assignment tables must store `creado_por` (FK to users) and `creado_en` (timestamp) for audit compliance
- Currency is always **UF (Unidad de Fomento)** for fixed components; percentages for variable MDR
- Transaction volumes are in **millones de pesos (MM CLP)**

### Database
- SQL relational database required (transaction support is mandatory)
- The `Transacciones_Mensual` table stores monthly aggregates only — not individual transactions
- `periodo` fields use the first day of the month format: `YYYY-MM-01`

### Testing Priorities
1. Resolution engine correctness (especially USO mechanism with tranche calculation)
2. Hierarchy precedence (SUCURSAL overrides COMERCIO overrides HOLDING)
3. Stackability logic between promotions
4. Validation rules (PRECIO_REBAJADO < BASE, MDR ranges, etc.)
5. Resolution engine performance (< 200ms SLA)

---

## Key Terminology Reference

| Spanish | English |
|---|---|
| Holding | Corporate group |
| Comercio | Merchant |
| Sucursal | Branch |
| Terminal | POS terminal |
| Tarifa Base | Base tariff / base rate |
| Beneficio | Benefit / promotion benefit |
| Adquisición | Acquisition (merchant onboarding) |
| Tramo | Tranche |
| Vigente | Active / in effect |
| Periodo | Billing period (month) |
| Monto | Amount |
| Arriendo | Rental (monthly POS terminal fee) |
| Cobro | Charge |
| Ahorro | Savings |
| UF | Unidad de Fomento (Chilean inflation-indexed unit) |
| MDR | Merchant Discount Rate |
| MCC | Merchant Category Code |
