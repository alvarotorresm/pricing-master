# PricingMaster — Tasks & Roadmap

## v1 — Scaffold Completo ✅ (current)

### Infrastructure
- [x] .gitignore, .env.example, requirements.txt
- [x] Dockerfile + docker-compose.yml (PostgreSQL 16 + FastAPI)
- [x] alembic.ini + alembic/env.py (async migrations)
- [x] app/config.py (Pydantic BaseSettings)

### Domain Core
- [x] app/core/enums.py (TerminalEstado, EntityType, TipoProducto, MecanismoActivacion, BeneficioPOS, BeneficioMDR)
- [x] app/core/exceptions.py (NotFoundError, ConflictError, BusinessRuleError)
- [x] app/db/base.py + app/db/session.py (async SQLAlchemy engine)

### Database Models (SQLAlchemy 2.x)
- [x] app/models/commercial.py (Holdings, Comercios, Sucursales, Terminales)
- [x] app/models/pos.py (POS_Tarifas, POS_Tarifa_Asignaciones)
- [x] app/models/mdr.py (MDR_Tarifas, MDR_Tarifa_Asignaciones)
- [x] app/models/promotions.py (Promotions, Promotion_Assignments)
- [x] app/models/transactions.py (Transacciones_Mensual)

### Schemas (Pydantic v2)
- [x] app/schemas/commercial.py
- [x] app/schemas/pos.py
- [x] app/schemas/mdr.py
- [x] app/schemas/promotions.py
- [x] app/schemas/resolucion.py

### Services & Resolution Engines
- [x] app/services/pos_service.py (POS CRUD + assignment)
- [x] app/services/mdr_service.py (MDR CRUD + assignment)
- [x] app/services/promotion_service.py (Promotions CRUD)
- [x] app/services/resolucion_pos.py ⚡ POS resolution engine
- [x] app/services/resolucion_mdr.py ⚡ MDR resolution engine

### API Routes (FastAPI)
- [x] app/api/commercial.py (Holdings, Comercios, Sucursales, Terminales)
- [x] app/api/pos_tarifas.py
- [x] app/api/mdr_tarifas.py
- [x] app/api/promotions.py
- [x] app/api/resolucion.py (/pos-resolucion + /mdr-resolucion)
- [x] app/main.py

### Tests
- [x] tests/conftest.py (async SQLite in-memory fixture)
- [x] tests/unit/test_pos_resolution.py (10 cases: ADQUISICION, USO tranches, PERMANENTE, hierarchy)
- [x] tests/unit/test_mdr_resolution.py (7 cases: USO, PERMANENTE_LIMITADO, FIJO/VARIABLE/MIXTO)
- [x] tests/unit/test_validations.py (business rule validations)

---

## v2 — Authentication & RBAC 🔒 (next)

### Users & Auth
- [ ] Add `users` table (id, email, password_hash, role, activo)
- [ ] JWT authentication (python-jose): POST /auth/login, POST /auth/register
- [ ] Auth dependency: `get_current_user()` injected in protected routes
- [ ] Connect `creado_por` FK in all assignment tables to `users.id`

### RBAC Roles
- [ ] `operador` — can create tariffs and promotions
- [ ] `supervisor` — can approve MDR changes; required for rate reductions to 0%
- [ ] `admin` — full access including user management

### Approval Workflow (MDR)
- [ ] Approval flow for MDR promotions reducing rate to 0% (requires supervisor role)
- [ ] `approval_status` field on MDR promotion assignments (PENDING, APPROVED, REJECTED)
- [ ] POST /mdr-promotions/{id}/approve (supervisor only)

---

## v3 — Audit & Compliance 📋

- [ ] `audit_logs` table (user_id, entity_type, entity_id, action, old_value, new_value, timestamp)
- [ ] Auto-log all MDR changes via SQLAlchemy events
- [ ] GET /audit-logs?entity_type=&entity_id= endpoint
- [ ] Export audit logs to CSV

---

## v4 — Frontend Dashboard 🖥️

- [ ] React + TypeScript scaffold (Vite)
- [ ] Dashboard: hierarchy view (Holding → Comercio → Sucursal → Terminal)
- [ ] POS tariff assignment UI
- [ ] MDR rate assignment UI
- [ ] Promotions management UI
- [ ] Resolution result viewer (search by terminal + period)

---

## v5 — Performance & Reliability 🚀

- [ ] Load test resolution engine (target: p99 < 200ms at 100 RPS)
- [ ] Add Redis caching for resolution engine (TTL = end of billing period)
- [ ] Add DB connection pooling configuration
- [ ] Monitoring: Prometheus metrics + Grafana dashboard
- [ ] Rate limiting on resolution endpoints

---

## Bugs / Tech Debt

_(Add items here as discovered)_
