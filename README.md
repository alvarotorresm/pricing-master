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
| Autenticación | JWT + RBAC |
| Tests | pytest + pytest-asyncio |
| Contenedores | Docker + Docker Compose |

---

## Estructura del proyecto

```
pricing-master/
├── app/
│   ├── api/                  # Routers FastAPI por dominio
│   │   ├── pos_tarifas.py
│   │   ├── mdr_tarifas.py
│   │   ├── promotions.py
│   │   └── resolucion.py     # Motor de resolución POS + MDR
│   ├── models/               # Modelos SQLAlchemy (11 tablas)
│   ├── schemas/              # Schemas Pydantic (request/response)
│   ├── services/             # Lógica de negocio y validaciones
│   ├── db.py                 # Sesión y engine de base de datos
│   └── main.py               # Entry point FastAPI
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
SECRET_KEY=your-secret-key
ENVIRONMENT=development
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
pytest                        # todos los tests
pytest tests/unit/            # solo lógica de negocio
pytest tests/integration/     # solo endpoints
pytest -k "resolucion"        # filtrar por nombre
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
- [`# Proyecto PricingMaster.md`](./%23%20Proyecto%20PricingMaster.md) — especificación completa de requerimientos (español)
