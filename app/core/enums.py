import enum


class TerminalEstado(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    BAJA = "BAJA"


class EntityType(str, enum.Enum):
    HOLDING = "HOLDING"
    COMERCIO = "COMERCIO"
    SUCURSAL = "SUCURSAL"


class TipoProducto(str, enum.Enum):
    POS = "POS"
    MDR = "MDR"


class MecanismoActivacion(str, enum.Enum):
    ADQUISICION = "ADQUISICION"
    USO = "USO"
    PERMANENTE_LIMITADO = "PERMANENTE_LIMITADO"
    PERMANENTE_ILIMITADO = "PERMANENTE_ILIMITADO"


class BeneficioPOS(str, enum.Enum):
    COSTO_CERO = "COSTO_CERO"
    PRECIO_REBAJADO = "PRECIO_REBAJADO"


class BeneficioMDR(str, enum.Enum):
    FIJO = "FIJO"
    VARIABLE = "VARIABLE"
    MIXTO = "MIXTO"
