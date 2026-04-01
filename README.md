# PricingMaster

Sistema de gestión de precios para adquirentes de medios de pago en el mercado chileno. Centraliza la configuración de **Tarifas POS** (arriendo mensual de terminales en UF) y **MDR (Merchant Discount Rate)** con soporte para jerarquías comerciales, promociones y un motor de resolución de tarifas en tiempo real.

---

## Stack

| Capa | Tecnología |
|---|---|
| API | Python 3.12 + FastAPI |
| ORM | SQLAlchemy 2.x |
| Migraciones | Alembic |
| Base de datos | PostgreSQL 16 |
| Validación | Pydantic v2 |
| Autenticación | Sin auth en v1 — JWT + RBAC en v2 |
| Tests | pytest + pytest-asyncio |
| Contenedores | Docker + Docker Compose |

---

## Quickstart

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Start services
docker compose up --build

# 3. Run migrations (first time only — handled automatically by docker compose)
docker compose exec api alembic upgrade head

# 4. Access
#   API:           http://localhost:8000
#   Swagger docs:  http://localhost:8000/docs
#   Health check:  http://localhost:8000/health
```

---

## Estructura del proyecto

```
pricing-master/
├── app/
│   ├── main.py               # Entry point FastAPI
│   ├── config.py             # Pydantic BaseSettings
│   ├── dependencies.py       # DB session injection
│   ├── core/
│   │   ├── enums.py          # ENUMs del dominio
│   │   └── exceptions.py     # HTTP exception wrappers
│   ├── db/
│   │   ├── base.py           # SQLAlchemy DeclarativeBase
│   │   └── session.py        # Async engine + session factory
│   ├── models/               # Modelos SQLAlchemy 2.x (11 tablas)
│   ├── schemas/              # Schemas Pydantic v2 (request/response)
│   ├── services/             # Lógica de negocio + motores de resolución
│   └── api/                  # Routers FastAPI por dominio
│       ├── pos_tarifas.py
│       ├── mdr_tarifas.py
│       ├── promotions.py
│       ├── commercial.py
│       └── resolucion.py     # Motor de resolución POS + MDR
├── alembic/                  # Migraciones de base de datos
├── tests/
│   ├── unit/                 # Tests del motor de resolución
│   └── integration/          # Tests de endpoints
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── CLAUDE.md
└── README.md
```

---

## Requisitos previos

- Python 3.12+
- Docker y Docker Compose
- PostgreSQL 16 (o usar el contenedor incluido)

---

## Instalación local

### 1. Clonar y configurar entorno

```bash
git clone https://github.com/alvarotorresm/pricing-master.git
cd pricing-master

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales de base de datos
```

Variables requeridas:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/pricingmaster
ENVIRONMENT=development
POSTGRES_DB=pricingmaster
POSTGRES_USER=pricing_user
POSTGRES_PASSWORD=pricing_pass
```

### 3. Base de datos

```bash
# Levantar PostgreSQL con Docker
docker compose up db -d

# Ejecutar migraciones
alembic upgrade head
```

### 4. Correr la API

```bash
uvicorn app.main:app --reload
```

API disponible en `http://localhost:8000`
Documentación interactiva en `http://localhost:8000/docs`

---

## Docker (entorno completo)

```bash
docker compose up --build
```

Levanta la API y PostgreSQL juntos. La API queda disponible en el puerto `8000`.

---

## Tests

```bash
# Instalar dependencias
pip install -r requirements.txt

# Todos los tests unitarios (26 tests)
pytest tests/unit/ -v

# Con cobertura
pytest tests/unit/ --cov=app/services --cov-report=term-missing

# Un archivo específico
pytest tests/unit/test_pos_resolution.py -v

# Filtrar por nombre
pytest -k "resolucion"
```

---

## API — Endpoints principales

Todos los endpoints están prefijados con `/api`.

### Motor de resolución (core)

```
GET /api/pos-resolucion?terminal_id=123&periodo=2026-02
GET /api/mdr-resolucion?terminal_id=123&periodo=2026-02
```

SLA: **< 200ms** de tiempo de respuesta.

### Tarifas POS

```
GET    /api/pos-tarifas
POST   /api/pos-tarifas
GET    /api/pos-tarifas/:id
PUT    /api/pos-tarifas/:id
POST   /api/pos-tarifa-asignaciones
GET    /api/pos-tarifa-asignaciones?entity_type=COMERCIO&entity_id=1
DELETE /api/pos-tarifa-asignaciones/:id
```

### Tarifas MDR

```
GET    /api/mdr-tarifas
POST   /api/mdr-tarifas
GET    /api/mdr-tarifas/:id
PUT    /api/mdr-tarifas/:id
POST   /api/mdr-tarifa-asignaciones
GET    /api/mdr-tarifa-asignaciones?entity_type=COMERCIO&entity_id=1
DELETE /api/mdr-tarifa-asignaciones/:id
```

### Promociones

```
GET    /api/promotions
POST   /api/promotions
POST   /api/promotion-assignments
GET    /api/promotion-assignments?entity_type=HOLDING&entity_id=5
DELETE /api/promotion-assignments/:id
```

---

## Modelo de entidades

```
Holdings (grupos corporativos)
  └── Comercios (merchants individuales)
        └── Sucursales (locales físicos)
              └── Terminales (POS físicos)
```

Precedencia de precios: **SUCURSAL > COMERCIO > HOLDING**

---

## Documentación adicional

- [`CLAUDE.md`](./CLAUDE.md) — contexto técnico detallado para asistentes AI
- [`TASKS.md`](./TASKS.md) — roadmap v1→v5 (auth, audit, frontend, performance)
- [`# Proyecto PricingMaster.md`](./%23%20Proyecto%20PricingMaster.md) — especificación completa de requerimientos (español)
