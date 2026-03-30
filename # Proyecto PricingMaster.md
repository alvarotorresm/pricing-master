# Documento de Requerimientos: Sistema de Gestión de Precios (PricingMaster)

---

## 1. Resumen del Proyecto

El sistema tiene como objetivo centralizar la gestión de precios para comercios, permitiendo la configuración dinámica de **Tarifas de POS** y **Merchant Discount Rate (MDR)**. La plataforma debe ser capaz de segmentar estos precios a nivel sucursal (local de un comercio), comercio individual (RUT del Comercio) o grupos comerciales (holdings/grupos económicos, de varios RUT del Comercio).

El modelo de precios POS se compone de dos capas independientes:
1. **Tarifa Base:** el precio fijo mensual de arriendo de terminal (en UF), asignable a nivel de holding, comercio o sucursal.
2. **Beneficio:** un descuento o exención sobre esa tarifa base, activado por un mecanismo de negocio (adquisición, uso, permanente).

---

## 2. Requerimientos Funcionales (RF)

### RF1: Gestión de Estructura Comercial

* **RF1.1 Creación de Comercios:** Registro de comercios individuales con identificadores únicos (ID, RUT del Comercio, Nombre de Fantasía).
* **RF1.2 Gestión de Holdings:** Capacidad de agrupar múltiples comercios bajo una misma entidad legal o corporativa para aplicar reglas de negocio globales. Los comercios pueden o no estar asociados a un holding. El holding es una entidad legal que puede tener uno o más comercios asociados. El holding también tiene un RUT.
* **RF1.3 Gestión de Sucursales:** Cada comercio debe tener al menos una sucursal. Las sucursales agrupan las terminales por ubicación física y constituyen el nivel más granular de asignación de promociones. Cada sucursal pertenece a un único comercio y debe tener al menos una terminal asociada.
* **RF1.4 Jerarquización:** Vinculación de comercios a holdings existentes y posibilidad de mover comercios entre diferentes grupos. Además, debe considerarse que un comercio puede tener múltiples sucursales, y cada sucursal puede tener múltiples terminales.
* **RF1.5 Gestión de Terminales:** Cada sucursal debe tener al menos una terminal. Las terminales son los puntos de venta físicos de un comercio. Cada terminal pertenece a una única sucursal y debe tener un identificador único.

### RF2: Motor de Tarifas

* **RF2.1 Gestión de Tarifas Base POS:** Catálogo de precios fijos mensuales de arriendo de terminal expresados en UF. Cada entidad (holding, comercio o sucursal) tiene asignada una tarifa base. La precedencia es `SUCURSAL` > `COMERCIO` > `HOLDING`. La tarifa base es la base sobre la cual se aplican los beneficios de las promociones POS. Las tarifas pueden ir entre 0,00 y 1,00UF mensuales, considerando 2 decimales. Estos deben ser seleccionados por el usuario desde un catálogo de tarifas base.
* **RF2.2 Configuración de Beneficios sobre Tarifa POS:** Definición de descuentos o exenciones aplicables sobre la tarifa base. Cada beneficio combina un **mecanismo de activación** con un **nivel de beneficio**, y puede configurarse a nivel de holding, comercio o sucursal individual.
  * **Creación de un Beneficio en el sistema:** Se pueden crear paquetes de beneficios que se aplicarán a una entidad (holding, comercio o sucursal) de forma permanente o temporal. Estos deben contener nombre, descripción, valor, nivel de aplicación (holding, comercio o sucursal), mecanismos de activación, tipo de beneficio, y fechas de inicio y fin de vigencia. Estos deben ser creados por el usuario desde la interfaz de usuario o cargados desde un archivo CSV.
  * **Mecanismos de activación:**
    * **Por adquisición:** se activa al momento de adquirir el servicio de adquirencia, por un tiempo determinado.
    * **Por uso:** se activa cuando el comercio supera X millones de pesos transaccionados en el mes. Se otorga un beneficio de 1 POS Costo Cero por cada X millones de pesos transaccionados.
    * **Permanente con límite de máquinas:** aplica de por vida hasta un número máximo de terminales definido, por ejemplo, 10 terminales. En este caso la fecha fin de vigencia es infinita.
    * **Permanente ilimitada:** aplica de por vida para todas las máquinas del comercio o holding. En este caso la fecha fin de vigencia es infinita.
  * **Tipos de beneficio:**
    * **POS Costo Cero:** el comercio no paga arriendo por el terminal (cobro = 0 UF). Aplica para todos los mecanismos de activación.
    * **POS Precio Rebajado:** el comercio paga un valor mensual reducido en UF, siempre menor a la tarifa base vigente. Aplica para todos los mecanismos de activación. Este beneficio debe ser menor a la tarifa base vigente.
  * **Niveles de beneficio:**
    * **Holding:** el beneficio se aplica a todos los comercios del holding.
    * **Comercio:** el beneficio se aplica a todos las sucursales del comercio.
    * **Sucursal:** el beneficio se aplica a todas las terminales de la sucursal.

* **RF2.3 Configuración de Beneficios sobre MDR:** Definición de descuentos aplicables sobre la tasa base de descuento que el adquirente cobra al comercio por procesar transacciones. Cada beneficio combina un **mecanismo de activación** con un **nivel de beneficio**, y puede configurarse a nivel de holding, comercio o sucursal individual.
  * **Creación de un Beneficio MDR en el sistema:** Se pueden crear paquetes de beneficios MDR que se aplicarán a una entidad (holding, comercio o sucursal) de forma permanente o temporal. Estos deben contener nombre, descripción, valor, nivel de aplicación (holding, comercio o sucursal), mecanismo de activación, tipo de beneficio, y fechas de inicio y fin de vigencia. Deben ser creados por el usuario desde la interfaz de usuario o cargados desde un archivo CSV.
  * **Mecanismos de activación:**
    * **Por adquisición:** se activa al momento de contratar el servicio de adquirencia, por un tiempo determinado.
    * **Por uso:** se activa cuando el comercio supera X millones de pesos transaccionados en el mes.
    * **Permanente con límite de volumen:** aplica de por vida mientras el comercio no supere un volumen mensual máximo definido. La fecha fin de vigencia es infinita pero se desactiva si se supera el umbral.
    * **Permanente ilimitada:** aplica de por vida para todas las transacciones del comercio o holding. La fecha fin de vigencia es infinita.
  * **Tipos de beneficio:**
    * **MDR Fijo:** se reduce o exime el componente fijo por transacción, expresado en UF. El valor resultante debe ser menor o igual al MDR fijo base vigente.
    * **MDR Variable:** se reduce el componente variable (porcentaje sobre monto de transacción). El valor resultante debe ser menor o igual al MDR variable base vigente.
    * **MDR Mixto:** se reduce simultáneamente el componente fijo (UF) y el componente variable (%). Ambos valores resultantes deben ser menores o iguales a sus respectivos valores base vigentes.
  * **Niveles de aplicación:**
    * **Holding:** el beneficio MDR se aplica a todos los comercios del holding.
    * **Comercio:** el beneficio MDR se aplica a todas las sucursales del comercio.
    * **Sucursal:** el beneficio MDR se aplica a todas las terminales de la sucursal.
* **RF2.4 Reglas de Aplicación:** Para POS: definir la tarifa base y el beneficio (con todo lo que implica). Para MDR: definir el MDR base y el beneficio (con todo lo que implica).

### RF3: Asignación y Ciclo de Vida

* **RF3.1 Registro de Promociones:** Vincular una promoción específica a un holding, a un comercio completo o a una sucursal individual. La promoción puede ser de POS o de MDR.
* **RF3.2 Actualización Dinámica:** Modificar condiciones de promociones vigentes sin interrumpir la operación.
* **RF3.3 Histórico de Cambios:** Registro de auditoría sobre quién modificó qué promoción y cuándo, y a qué comercio o holding se aplicó.

---

## 3. Modelo de Entidades

| Entidad | Descripción | Relación |
| --- | --- | --- |
| **Holding** | Grupo corporativo superior. | 1 : N con Comercios |
| **Comercio** | Comercio individual / Merchant. | N : 1 con Holding (nullable) |
| **Sucursal** | Ubicación física de un comercio. | N : 1 con Comercio |
| **Terminal** | POS físico de una sucursal. | N : 1 con Sucursal |
| **POS_Tarifas** | Catálogo de tarifas fijas mensuales de arriendo POS (en UF, 0.00–1.00). | Asignada vía POS_Tarifa_Asignaciones |
| **POS_Tarifa_Asignaciones** | Vincula una tarifa POS base a un holding, comercio o sucursal. | FK a POS_Tarifas + entidad destino |
| **MDR_Tarifas** | Catálogo de tasas base MDR (componente fijo en UF + componente variable en %). | Asignada vía MDR_Tarifa_Asignaciones |
| **MDR_Tarifa_Asignaciones** | Vincula una tarifa MDR base a un holding, comercio o sucursal. | FK a MDR_Tarifas + entidad destino |
| **Promotions** | Catálogo de beneficios POS y MDR (mecanismo de activación + tipo de beneficio). | Asignada vía Promotion_Assignments |
| **Promotion_Assignments** | Registro de activación de un beneficio para una entidad. | FK a Promotions + entidad destino |
| **Transacciones_Mensual** | Agregado mensual de transacciones por terminal. | N : 1 con Terminal y Sucursal |

---

## 4. Requerimientos No Funcionales (RNF)

* **Seguridad:** Control de acceso basado en roles (RBAC) para diferenciar quién crea promociones y quién las aprueba.
* **Integridad de Datos:** Los cálculos de MDR deben soportar hasta 4 decimales para evitar errores de liquidación financiera. El sistema debe validar que `valor_cobro_uf (PRECIO_REBAJADO) < tarifa_base.valor_mensual_uf` al momento de crear la asignación.
* **Disponibilidad:** El motor de resolución de tarifas debe responder en menos de **200ms** para no afectar el flujo de la transacción en el POS.

---

## 5. Casos de Uso Principales

1. **Alta de Holding:** Un administrador crea el "Grupo Retail X", le asigna 50 tiendas y le configura una tarifa base POS de 0.65 UF/mes.
2. **Campaña de Fidelización:** Se crea una promo de MDR reducido para todo el "Grupo Retail X" durante el Black Friday. Se crea una promo de POS Costo Cero, por uso, para todos los comercios del "Grupo Retail X".
3. **Ajuste Particular:** Un comercio específico del holding negocia una tarifa base propia (override) y recibe adicionalmente un PRECIO_REBAJADO permanente, de forma independiente al resto del grupo.

---

## 6. Modelo de Datos (ERD)

### A. Tabla: `Holdings`

Representa a los grupos económicos (ej. Cencosud, Holding Retail X).

* `id` (PK)
* `nombre`
* `rut_holding` (RUT)
* `segmento` (Ej. Grande, Mediano)

### B. Tabla: `Comercios`

Los comercios individuales que pertenecen (o no) a un holding.

* `id` (PK)
* `rut_comercio` (RUT)
* `nombre_fantasia`
* `holding_id` (FK → `Holdings.id`, nullable — un comercio puede ser independiente)
* `external_id` (ID del core transaccional o POS)
* `mcc` (Merchant Category Code — útil para segmentar promos por rubro)

### C. Tabla: `Sucursales`

Cada comercio tiene al menos una sucursal. Agrupa las terminales por ubicación física.

* `id` (PK)
* `comercio_id` (FK → `Comercios.id`, NOT NULL)
* `nombre`
* `direccion`

### D. Tabla: `Terminales`

Registra cada terminal POS físico. Cada terminal pertenece a una sucursal (y por derivación, a un comercio y holding).

* `id` (PK)
* `sucursal_id` (FK → `Sucursales.id`, NOT NULL)
* `external_terminal_id` (ID del sistema POS origen)
* `fecha_adquisicion` (Date — base para evaluar `POS_ADQUISICION`)
* `estado` (ENUM: `'ACTIVO'`, `'INACTIVO'`, `'BAJA'`)

### E. Tabla: `POS_Tarifas` (Catálogo de Tarifas Base POS)

Define los planes de precio fijo mensual de arriendo disponibles. Rango válido: 0.00–1.00 UF. Catálogo versionable; nunca se borran registros.

| Campo              | Tipo            | Descripción                                                    |
|--------------------|-----------------|----------------------------------------------------------------|
| `id`               | PK              |                                                                |
| `nombre`           | VARCHAR         | Ej: "Tarifa Estándar 2026", "Tarifa Premium Retail"            |
| `valor_mensual_uf` | Decimal(4,2)    | Costo mensual de arriendo por terminal en UF (0.00–1.00)       |
| `descripcion`      | TEXT            | Notas internas                                                 |
| `vigente_desde`    | Date            | Desde cuándo aplica en el catálogo                             |
| `vigente_hasta`    | Date (nullable) | NULL = sigue vigente; fecha = fue reemplazada                  |
| `activa`           | Boolean         | Soft delete                                                    |
| `creado_por`       | FK → Usuarios   | Auditoría                                                      |
| `creado_en`        | Timestamp       |                                                                |

**Ejemplo de datos del catálogo:**
```
id=1  nombre="Tarifa Estándar 2026"   valor_mensual_uf=0.89
id=2  nombre="Tarifa Premium Retail"  valor_mensual_uf=0.65
id=3  nombre="Tarifa PyME"            valor_mensual_uf=1.00
```

### F. Tabla: `POS_Tarifa_Asignaciones`

Vincula una tarifa POS base a un holding, comercio o sucursal. Precedencia: `SUCURSAL` > `COMERCIO` > `HOLDING`.

| Campo          | Tipo                                          | Descripción                                             |
|----------------|-----------------------------------------------|---------------------------------------------------------|
| `id`           | PK                                            |                                                         |
| `tarifa_id`    | FK → `POS_Tarifas.id`                         |                                                         |
| `entity_type`  | ENUM(`'HOLDING'`, `'COMERCIO'`, `'SUCURSAL'`) | Nivel de aplicación                                     |
| `entity_id`    | Integer                                       | ID del holding, comercio o sucursal según `entity_type` |
| `fecha_inicio` | Date                                          | Desde cuándo aplica                                     |
| `fecha_fin`    | Date (nullable)                               | NULL = indefinida                                       |
| `prioridad`    | Integer                                       | Desempate si hay dos asignaciones activas simultáneas   |
| `creado_por`   | FK → Usuarios                                 |                                                         |
| `creado_en`    | Timestamp                                     |                                                         |

### G. Tabla: `MDR_Tarifas` (Catálogo de Tasas Base MDR)

Define los planes de tasa base MDR disponibles. Compuesto por un componente fijo (UF por transacción) y/o un componente variable (% sobre monto). Catálogo versionable; nunca se borran registros.

| Campo                | Tipo            | Descripción                                                                |
|----------------------|-----------------|----------------------------------------------------------------------------|
| `id`                 | PK              |                                                                            |
| `nombre`             | VARCHAR         | Ej: "MDR Estándar Retail", "MDR Premium PyME"                              |
| `valor_fijo_uf`      | Decimal(10,4)   | Componente fijo por transacción en UF (nullable si solo aplica variable)   |
| `valor_variable_pct` | Decimal(6,4)    | Componente variable en % sobre monto (nullable si solo aplica fijo)        |
| `descripcion`        | TEXT            | Notas internas                                                             |
| `vigente_desde`      | Date            | Desde cuándo aplica en el catálogo                                         |
| `vigente_hasta`      | Date (nullable) | NULL = sigue vigente; fecha = fue reemplazada                              |
| `activa`             | Boolean         | Soft delete                                                                |
| `creado_por`         | FK → Usuarios   | Auditoría                                                                  |
| `creado_en`          | Timestamp       |                                                                            |

**Ejemplo de datos del catálogo:**
```
id=1  nombre="MDR Estándar"      valor_fijo_uf=0.0010  valor_variable_pct=1.2500
id=2  nombre="MDR Premium"       valor_fijo_uf=0.0005  valor_variable_pct=0.9900
id=3  nombre="MDR Solo Variable" valor_fijo_uf=null     valor_variable_pct=1.5000
```

### H. Tabla: `MDR_Tarifa_Asignaciones`

Vincula una tarifa MDR base a un holding, comercio o sucursal. Misma lógica de precedencia que `POS_Tarifa_Asignaciones`: `SUCURSAL` > `COMERCIO` > `HOLDING`.

| Campo          | Tipo                                          | Descripción                                             |
|----------------|-----------------------------------------------|---------------------------------------------------------|
| `id`           | PK                                            |                                                         |
| `tarifa_id`    | FK → `MDR_Tarifas.id`                         |                                                         |
| `entity_type`  | ENUM(`'HOLDING'`, `'COMERCIO'`, `'SUCURSAL'`) | Nivel de aplicación                                     |
| `entity_id`    | Integer                                       | ID del holding, comercio o sucursal según `entity_type` |
| `fecha_inicio` | Date                                          | Desde cuándo aplica                                     |
| `fecha_fin`    | Date (nullable)                               | NULL = indefinida                                       |
| `prioridad`    | Integer                                       | Desempate si hay dos asignaciones activas simultáneas   |
| `creado_por`   | FK → Usuarios                                 |                                                         |
| `creado_en`    | Timestamp                                     |                                                         |

### I. Tabla: `Promotions` (Catálogo de Beneficios)

Define el beneficio que se aplica sobre la tarifa base (POS o MDR). Separa el **producto** del **mecanismo de activación** y el **tipo de beneficio** para máxima flexibilidad.

| Campo                  | Tipo                                                                              | Descripción                                                                                 |
|------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `id`                   | PK                                                                                |                                                                                             |
| `nombre`               | VARCHAR                                                                           | Nombre del beneficio                                                                        |
| `descripcion`          | TEXT                                                                              |                                                                                             |
| `tipo_producto`        | ENUM(`'POS'`, `'MDR'`)                                                            | A qué producto aplica                                                                       |
| `mecanismo_activacion` | ENUM(`'ADQUISICION'`, `'USO'`, `'PERMANENTE_LIMITADO'`, `'PERMANENTE_ILIMITADO'`) | Condición que activa el beneficio                                                           |
| `beneficio_pos`        | ENUM(`'COSTO_CERO'`, `'PRECIO_REBAJADO'`, nullable)                               | Solo cuando `tipo_producto='POS'`                                                           |
| `valor_cobro_uf`       | Decimal(4,2), nullable                                                            | Solo cuando `beneficio_pos='PRECIO_REBAJADO'`; siempre < tarifa POS base vigente (0.00–1.00) |
| `beneficio_mdr`        | ENUM(`'FIJO'`, `'VARIABLE'`, `'MIXTO'`, nullable)                                 | Solo cuando `tipo_producto='MDR'`                                                           |
| `valor_fijo_uf`        | Decimal(10,4), nullable                                                           | MDR fijo beneficiado en UF; solo si `beneficio_mdr` es `'FIJO'` o `'MIXTO'`                |
| `valor_variable_pct`   | Decimal(6,4), nullable                                                            | MDR variable beneficiado en %; solo si `beneficio_mdr` es `'VARIABLE'` o `'MIXTO'`         |
| `duracion_dias`        | Integer, nullable                                                                 | Para `ADQUISICION`: días de vigencia del beneficio desde la fecha de adquisición            |
| `umbral_monto_mm`      | Decimal, nullable                                                                 | Para `USO`: tamaño del tramo en millones de pesos. Por cada tramo completo alcanzado se libera `pos_por_tramo` terminales con beneficio |
| `pos_por_tramo`        | Integer, nullable, default 1                                                      | Solo para POS `USO`: cuántas terminales reciben el beneficio por cada tramo de `umbral_monto_mm` completado. Ej: 1 POS por cada 8 MM |
| `max_pos_beneficio`    | Integer, nullable                                                                 | Solo para POS `USO`: tope máximo de terminales que pueden recibir el beneficio. Si null, el tope es el total de terminales activas en el alcance |
| `max_terminales`       | Integer, nullable                                                                 | Para POS `PERMANENTE_LIMITADO`: número máximo de terminales cubiertas                      |
| `max_volumen_mm`       | Decimal, nullable                                                                 | Para MDR `PERMANENTE_LIMITADO`: beneficio activo mientras volumen mensual < max_volumen_mm  |
| `is_stackable`         | Boolean, default `false`                                                          | Si `true`, se acumula con otras promos vigentes del mismo nivel                             |
| `fecha_inicio`         | Date, nullable                                                                    | NULL en promos permanentes                                                                  |
| `fecha_fin`            | Date, nullable                                                                    | NULL en promos permanentes                                                                  |

### J. Tabla: `Promotion_Assignments`

Vincula un beneficio con la entidad que lo recibe.

* `id` (PK)
* `promotion_id` (FK → `Promotions.id`)
* `entity_type` (ENUM: `'HOLDING'`, `'COMERCIO'`, `'SUCURSAL'` — precedencia: `SUCURSAL` > `COMERCIO` > `HOLDING`)
* `entity_id` (FK → `Holdings.id`, `Comercios.id` o `Sucursales.id` según `entity_type`)
* `prioridad` (Integer — desempate entre promos del mismo `entity_type`; mayor valor = mayor prioridad)

### K. Tabla: `Transacciones_Mensual`

Agregado mensual de transacciones por terminal. No almacena registros individuales; solo el resumen necesario para evaluar condiciones de activación por uso y por volumen.

* `id` (PK)
* `terminal_id` (FK → `Terminales.id`)
* `sucursal_id` (FK → `Sucursales.id`)
* `periodo` (Date — primer día del mes, ej. `2026-02-01`)
* `monto_total_mm` (Decimal — suma de transacciones del mes en millones de pesos; usado para `USO` y `PERMANENTE_LIMITADO` MDR)
* `num_transacciones` (Integer)

---

## 7. Lógica de Resolución POS (Tarifa Base + Beneficio)

### Diagrama conceptual

```
POS_Tarifas ────── POS_Tarifa_Asignaciones
                          │
                          ├── HOLDING  → valor_mensual_uf (menor precedencia)
                          ├── COMERCIO → valor_mensual_uf (override de holding)
                          └── SUCURSAL → valor_mensual_uf (mayor precedencia)
                                │
                                ▼
                          [ TARIFA BASE POS ]
                                │
                                │  aplicar beneficio POS (si existe y está activado)
                                ▼
Promotions (tipo_producto='POS') ── Promotion_Assignments
                          │
                          ├── COSTO_CERO      → cobro = 0.00 UF
                          └── PRECIO_REBAJADO → cobro = valor_cobro_uf (< tarifa_base)
```

### Pseudocódigo de resolución

```
ENTRADA: terminal_id, periodo (mes/año)

PASO 1 — Obtener la Tarifa Base POS:
  Buscar en POS_Tarifa_Asignaciones activas (fecha_inicio <= periodo <= fecha_fin):
  1a. entity_type='SUCURSAL'  AND entity_id = terminal.sucursal_id  → si existe, usar. FIN.
  1b. entity_type='COMERCIO'  AND entity_id = sucursal.comercio_id  → si existe, usar. FIN.
  1c. entity_type='HOLDING'   AND entity_id = comercio.holding_id   → si existe, usar. FIN.
  1d. Sin asignación → usar tarifa_default del sistema (configurable).

PASO 2 — Obtener el Beneficio POS Vigente (misma jerarquía SUCURSAL > COMERCIO > HOLDING):
  Filtrar Promotion_Assignments donde promotion.tipo_producto='POS'.
  Evaluar condición de activación según mecanismo_activacion:

  ADQUISICION:
    vigente si (hoy − terminal.fecha_adquisicion) <= promo.duracion_dias

  USO (cálculo graduado por tramos):
    monto_mes    = Transacciones_Mensual.monto_total_mm del alcance (sucursal/comercio/holding)
    tramos       = floor(monto_mes / promo.umbral_monto_mm)
    n_beneficio  = min(
                     tramos * (promo.pos_por_tramo ?? 1),
                     promo.max_pos_beneficio ?? count_terminales_ACTIVO_en_alcance
                   )
    Ordenar terminales activas del alcance por fecha_adquisicion ASC (más antiguas primero).
    La terminal tiene beneficio si su posición en el ranking <= n_beneficio.

  PERMANENTE_LIMITADO:
    vigente si count(terminales ACTIVO en sucursal) <= promo.max_terminales

  PERMANENTE_ILIMITADO:
    siempre vigente

PASO 3 — Calcular Cobro Final POS:
  Sin beneficio vigente → cobro = tarifa_base.valor_mensual_uf
  COSTO_CERO            → cobro = 0.00 UF
  PRECIO_REBAJADO       → cobro = promo.valor_cobro_uf

SALIDA: { cobro_final_uf, tarifa_base_uf, beneficio_aplicado, n_terminales_beneficiadas, ahorro_uf }
```

### Casos de uso ilustrativos

**Caso A — Holding con tarifa preferencial + COSTO_CERO por adquisición (90 días)**
```
POS_Tarifa_Asignaciones: tarifa=0.65 UF → HOLDING Grupo_Retail_X
Promotion_Assignments:   tipo_producto=POS, mecanismo=ADQUISICION, beneficio_pos=COSTO_CERO,
                         duracion_dias=90 → HOLDING Grupo_Retail_X

Terminal nueva (día 30):  tarifa_base=0.65 → COSTO_CERO activo → cobro = 0.00 UF
Terminal vieja (día 120): tarifa_base=0.65 → sin beneficio      → cobro = 0.65 UF
```

**Caso B — Comercio con tarifa override + PRECIO_REBAJADO permanente**
```
POS_Tarifa_Asignaciones: tarifa=0.89 UF → HOLDING Holding_A
                         tarifa=0.45 UF → COMERCIO Comercio_B  ← override

Promotion_Assignments: tipo_producto=POS, mecanismo=PERMANENTE_ILIMITADO,
                        beneficio_pos=PRECIO_REBAJADO, valor_cobro_uf=0.20 → COMERCIO Comercio_B

Resolución: tarifa_base=0.45 (COMERCIO > HOLDING) → PRECIO_REBAJADO=0.20 (0.20 < 0.45 ✓) → cobro=0.20 UF
```

**Caso C — Comercio con 3 POS, COSTO_CERO graduado por volumen (1 POS cada 8 MM)**
```
Contexto: comercio con 3 terminales activas (T1 más antigua, T3 más reciente).
POS_Tarifa_Asignaciones: tarifa=0.89 UF → COMERCIO Comercio_X
Promotions:              tipo_producto=POS, mecanismo=USO, beneficio_pos=COSTO_CERO,
                         umbral_monto_mm=8.0, pos_por_tramo=1, max_pos_beneficio=null

Mes con  5 MM transaccionados:  tramos=floor(5/8)=0   → n_beneficio=0 → T1,T2,T3 pagan 0.89 UF
Mes con  8 MM transaccionados:  tramos=floor(8/8)=1   → n_beneficio=1 → T1: 0.00 UF, T2,T3: 0.89 UF
Mes con 23 MM transaccionados:  tramos=floor(23/8)=2  → n_beneficio=2 → T1,T2: 0.00 UF, T3: 0.89 UF
Mes con 40 MM transaccionados:  tramos=floor(40/8)=5  → n_beneficio=min(5,3)=3 → T1,T2,T3: 0.00 UF
```

---

## 8. Lógica de Resolución MDR (Tasa Base + Beneficio)

### Diagrama conceptual

```
MDR_Tarifas ────── MDR_Tarifa_Asignaciones
                          │
                          ├── HOLDING  → valor_fijo_uf + valor_variable_pct (menor precedencia)
                          ├── COMERCIO → valor_fijo_uf + valor_variable_pct (override de holding)
                          └── SUCURSAL → valor_fijo_uf + valor_variable_pct (mayor precedencia)
                                │
                                ▼
                          [ TASA BASE MDR ]
                                │
                                │  aplicar beneficio MDR (si existe y está activado)
                                ▼
Promotions (tipo_producto='MDR') ── Promotion_Assignments
                          │
                          ├── FIJO     → aplica valor_fijo_uf beneficiado (< tasa_base.valor_fijo_uf)
                          ├── VARIABLE → aplica valor_variable_pct beneficiado (< tasa_base.valor_variable_pct)
                          └── MIXTO    → aplica ambos componentes beneficiados
```

### Pseudocódigo de resolución

```
ENTRADA: terminal_id, periodo (mes/año)

PASO 1 — Obtener la Tasa Base MDR:
  Buscar en MDR_Tarifa_Asignaciones activas (fecha_inicio <= periodo <= fecha_fin):
  1a. entity_type='SUCURSAL'  AND entity_id = terminal.sucursal_id  → si existe, usar. FIN.
  1b. entity_type='COMERCIO'  AND entity_id = sucursal.comercio_id  → si existe, usar. FIN.
  1c. entity_type='HOLDING'   AND entity_id = comercio.holding_id   → si existe, usar. FIN.
  1d. Sin asignación → usar tasa_mdr_default del sistema (configurable).

PASO 2 — Obtener el Beneficio MDR Vigente (misma jerarquía SUCURSAL > COMERCIO > HOLDING):
  Filtrar Promotion_Assignments donde promotion.tipo_producto='MDR'.
  Evaluar condición de activación según mecanismo_activacion:
    ADQUISICION          → vigente si (hoy − terminal.fecha_adquisicion) <= promo.duracion_dias
    USO                  → vigente si Transacciones_Mensual.monto_total_mm >= promo.umbral_monto_mm
    PERMANENTE_LIMITADO  → vigente si Transacciones_Mensual.monto_total_mm < promo.max_volumen_mm
                           (se desactiva si se supera el volumen máximo)
    PERMANENTE_ILIMITADO → siempre vigente

PASO 3 — Calcular Tasa Final MDR:
  Sin beneficio vigente:
    fijo_final    = tasa_base.valor_fijo_uf
    variable_final = tasa_base.valor_variable_pct
  Beneficio FIJO:
    fijo_final    = promo.valor_fijo_uf    (< tasa_base.valor_fijo_uf)
    variable_final = tasa_base.valor_variable_pct  (sin cambio)
  Beneficio VARIABLE:
    fijo_final    = tasa_base.valor_fijo_uf  (sin cambio)
    variable_final = promo.valor_variable_pct  (< tasa_base.valor_variable_pct)
  Beneficio MIXTO:
    fijo_final    = promo.valor_fijo_uf    (< tasa_base.valor_fijo_uf)
    variable_final = promo.valor_variable_pct  (< tasa_base.valor_variable_pct)

SALIDA: { fijo_final_uf, variable_final_pct, tasa_base, beneficio_aplicado }
```

### Casos de uso ilustrativos

**Caso D — Holding con beneficio MDR VARIABLE por adquisición (180 días)**
```
MDR_Tarifa_Asignaciones: tasa_base → fijo=0.0010 UF, variable=1.25% → HOLDING Grupo_Retail_X
Promotion_Assignments:   tipo_producto=MDR, mecanismo=ADQUISICION, beneficio_mdr=VARIABLE,
                         valor_variable_pct=0.90, duracion_dias=180 → HOLDING Grupo_Retail_X

Terminal nueva (día 60):  base=1.25% → VARIABLE activo → variable_final=0.90%, fijo_final=0.0010 UF
Terminal vieja (día 200): base=1.25% → sin beneficio   → variable_final=1.25%, fijo_final=0.0010 UF
```

**Caso E — Comercio con beneficio MDR MIXTO permanente**
```
MDR_Tarifa_Asignaciones: tasa_base → fijo=0.0010 UF, variable=1.25% → HOLDING Holding_A
                          tasa_base → fijo=0.0008 UF, variable=1.10% → COMERCIO Comercio_B ← override

Promotion_Assignments: tipo_producto=MDR, mecanismo=PERMANENTE_ILIMITADO, beneficio_mdr=MIXTO,
                        valor_fijo_uf=0.0003, valor_variable_pct=0.75 → COMERCIO Comercio_B

Resolución: tasa_base=Comercio_B (COMERCIO > HOLDING)
            → MIXTO: fijo_final=0.0003 (0.0003 < 0.0008 ✓), variable_final=0.75% (0.75 < 1.10 ✓)
```

**Caso F — PyME con beneficio MDR FIJO mientras no supere volumen mensual**
```
MDR_Tarifa_Asignaciones: tasa_base → fijo=0.0010 UF, variable=1.25% → COMERCIO PyME_X
Promotion_Assignments:   tipo_producto=MDR, mecanismo=PERMANENTE_LIMITADO, beneficio_mdr=FIJO,
                         valor_fijo_uf=0.0000, max_volumen_mm=50.0 → COMERCIO PyME_X

Mes con 35 MM transaccionados:  35 < 50.0 ✓ → fijo_final=0.0000, variable_final=1.25%
Mes con 62 MM transaccionados:  62 >= 50.0 ✗ → fijo_final=0.0010, variable_final=1.25%
```

---

## 9. Lógica de Aplicación (Herencia y Conflictos entre Beneficios)

Cuando Holding, Comercio y Sucursal tienen beneficios distintos asignados:

* **Regla de Override:** `SUCURSAL` > `COMERCIO` > `HOLDING`. El nivel más específico suprime los de nivel superior.
* **Acumulación:** controlada por `is_stackable` en `Promotions`. Si `true`, coexiste con otras promos vigentes del mismo nivel. Si `false`, compite y solo se aplica la de mayor `prioridad` en `Promotion_Assignments`.

**Jerarquía de cálculo:**
1. Obtener asignaciones activas con `entity_type='SUCURSAL'` AND `entity_id = terminal.sucursal_id`.
2. Si existen → usar esas; suprimir COMERCIO y HOLDING para esta terminal.
3. Si no → obtener `entity_type='COMERCIO'` AND `entity_id = sucursal.comercio_id`.
4. Si existen → usar esas; suprimir HOLDING.
5. Si no → obtener `entity_type='HOLDING'` AND `entity_id = comercio.holding_id`.
6. Sobre el conjunto resultante: si todas tienen `is_stackable=true`, aplicar todas; si alguna tiene `is_stackable=false`, aplicar solo la de mayor `prioridad`.

---

## 10. Validaciones de Negocio

| Regla | Aplica a | Descripción |
|---|---|---|
| `POS: PRECIO_REBAJADO < BASE` | POS | Al crear una promo PRECIO_REBAJADO, validar que `valor_cobro_uf < POS_Tarifas.valor_mensual_uf` vigente para la entidad objetivo. Validación en capa de servicio. |
| `POS: rango tarifa base` | POS | `POS_Tarifas.valor_mensual_uf` debe estar entre 0.00 y 1.00 UF (2 decimales). |
| `MDR: FIJO beneficiado < base` | MDR | Si `beneficio_mdr` es `'FIJO'` o `'MIXTO'`, validar que `valor_fijo_uf < MDR_Tarifas.valor_fijo_uf` vigente. |
| `MDR: VARIABLE beneficiado < base` | MDR | Si `beneficio_mdr` es `'VARIABLE'` o `'MIXTO'`, validar que `valor_variable_pct < MDR_Tarifas.valor_variable_pct` vigente. |
| `POS USO: pos_por_tramo >= 1` | POS | Si `mecanismo_activacion='USO'` y `tipo_producto='POS'`, `pos_por_tramo` debe ser >= 1 y `umbral_monto_mm` debe ser > 0. |
| `POS USO: max_pos_beneficio coherente` | POS | Si se define `max_pos_beneficio`, debe ser >= `pos_por_tramo` y se recomienda que no supere el número de terminales activas del alcance al momento de crear la asignación. |
| `UNA TARIFA BASE ACTIVA` | POS y MDR | Una entidad no puede tener dos asignaciones de tarifa base activas simultáneamente para el mismo período (aplica por separado a POS y MDR). |
| `SOFT DELETE obligatorio` | POS y MDR | Tarifas y promos nunca se borran. Se marcan `activa=false` o se registra `fecha_fin`. |
| `VERSIONING` | POS y MDR | Cambios en valores de `POS_Tarifas` o `MDR_Tarifas` crean un nuevo registro; no modifican el anterior. |

---

## 11. Requerimientos Técnicos de Auditoría

Al tocar el **MDR (Merchant Discount Rate)**, estás tocando dinero y liquidaciones. El sistema **debe** incluir:

1. **Versioning de Promos:** No se borran promos; se crean versiones o se marcan como inactivas. Si una promo cambió ayer, debe ser posible ver qué tasa se aplicó en una transacción de hace un mes.
2. **Logs de Usuario:** Registro de quién aprobó un cambio de tasa (indispensable para cumplimiento y prevención de fraude).
3. **Workflow de Aprobación:** Las promociones de MDR que superen cierto umbral (ej. bajar la tasa a 0%) deben requerir aprobación de un usuario con rol "Supervisión".

---

## 12. Flujo de Onboarding

1. **Ingreso:** Se crea el comercio en el sistema.
2. **Validación de Holding:** El sistema detecta por RUT o Nombre si pertenece a un Holding existente.
3. **Asignación Automática:** Si el Holding tiene una tarifa base y/o promo de "Bienvenida" activa, el nuevo comercio las hereda desde el minuto 1 sin intervención manual.

---

## 13. API REST

### Tarifas Base POS

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET    | `/api/pos-tarifas` | Listar catálogo de tarifas base POS |
| POST   | `/api/pos-tarifas` | Crear nueva tarifa base POS |
| GET    | `/api/pos-tarifas/:id` | Detalle de una tarifa POS |
| PUT    | `/api/pos-tarifas/:id` | Actualizar (crea versión nueva en el catálogo) |
| POST   | `/api/pos-tarifa-asignaciones` | Asignar tarifa POS base a holding/comercio/sucursal |
| GET    | `/api/pos-tarifa-asignaciones?entity_type=&entity_id=` | Ver tarifa POS vigente de una entidad |
| DELETE | `/api/pos-tarifa-asignaciones/:id` | Desactivar asignación POS (registra `fecha_fin`) |

### Tarifas Base MDR

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET    | `/api/mdr-tarifas` | Listar catálogo de tasas base MDR |
| POST   | `/api/mdr-tarifas` | Crear nueva tasa base MDR |
| GET    | `/api/mdr-tarifas/:id` | Detalle de una tasa MDR |
| PUT    | `/api/mdr-tarifas/:id` | Actualizar (crea versión nueva en el catálogo) |
| POST   | `/api/mdr-tarifa-asignaciones` | Asignar tasa MDR base a holding/comercio/sucursal |
| GET    | `/api/mdr-tarifa-asignaciones?entity_type=&entity_id=` | Ver tasa MDR vigente de una entidad |
| DELETE | `/api/mdr-tarifa-asignaciones/:id` | Desactivar asignación MDR (registra `fecha_fin`) |

### Beneficios / Promociones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET    | `/api/promotions` | Listar catálogo de beneficios (filtrables por `tipo_producto`) |
| POST   | `/api/promotions` | Crear nuevo beneficio POS o MDR |
| POST   | `/api/promotion-assignments` | Asignar beneficio a holding/comercio/sucursal |
| GET    | `/api/promotion-assignments?entity_type=&entity_id=` | Ver beneficios vigentes de una entidad |
| DELETE | `/api/promotion-assignments/:id` | Desactivar asignación de beneficio |

### Motor de Resolución

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET    | `/api/pos-resolucion?terminal_id=&periodo=2026-02` | Tarifa POS base + beneficio + cobro final por terminal |
| GET    | `/api/mdr-resolucion?terminal_id=&periodo=2026-02` | Tasa MDR base + beneficio + tasas finales por terminal |

**Ejemplo de respuesta de `/api/pos-resolucion`:**

```json
{
  "terminal_id": 123,
  "periodo": "2026-02",
  "tarifa_base": {
    "id": 2,
    "nombre": "Tarifa Premium Retail",
    "valor_mensual_uf": 0.65
  },
  "beneficio_aplicado": {
    "promotion_id": 7,
    "tipo_producto": "POS",
    "mecanismo_activacion": "ADQUISICION",
    "beneficio_pos": "COSTO_CERO",
    "activacion": "dias_desde_adquisicion=30, limite=90",
    "vigente": true
  },
  "cobro_final_uf": 0.00,
  "ahorro_uf": 0.65
}
```

**Ejemplo de respuesta de `/api/mdr-resolucion`:**

```json
{
  "terminal_id": 123,
  "periodo": "2026-02",
  "tasa_base": {
    "id": 1,
    "nombre": "MDR Estándar",
    "valor_fijo_uf": 0.0010,
    "valor_variable_pct": 1.2500
  },
  "beneficio_aplicado": {
    "promotion_id": 12,
    "tipo_producto": "MDR",
    "mecanismo_activacion": "PERMANENTE_ILIMITADO",
    "beneficio_mdr": "MIXTO",
    "vigente": true
  },
  "fijo_final_uf": 0.0003,
  "variable_final_pct": 0.7500
}
```

**Ejemplo de petición para asignar un beneficio MDR a un holding:**

```json
{
  "promotion_id": 12,
  "entity_type": "HOLDING",
  "entity_id": 77821,
  "fecha_inicio": "2026-01-01",
  "fecha_fin": "2026-03-31",
  "prioridad": 10
}
```
