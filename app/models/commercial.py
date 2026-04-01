from datetime import date
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Date, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.core.enums import TerminalEstado


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    rut_holding: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    segmento: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    comercios: Mapped[List["Comercio"]] = relationship("Comercio", back_populates="holding")


class Comercio(Base):
    __tablename__ = "comercios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rut_comercio: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    nombre_fantasia: Mapped[str] = mapped_column(String(255), nullable=False)
    holding_id: Mapped[Optional[int]] = mapped_column(ForeignKey("holdings.id"), nullable=True, index=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mcc: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    holding: Mapped[Optional["Holding"]] = relationship("Holding", back_populates="comercios")
    sucursales: Mapped[List["Sucursal"]] = relationship("Sucursal", back_populates="comercio")


class Sucursal(Base):
    __tablename__ = "sucursales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comercio_id: Mapped[int] = mapped_column(ForeignKey("comercios.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    direccion: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    comercio: Mapped["Comercio"] = relationship("Comercio", back_populates="sucursales")
    terminales: Mapped[List["Terminal"]] = relationship("Terminal", back_populates="sucursal")


class Terminal(Base):
    __tablename__ = "terminales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), nullable=False, index=True)
    external_terminal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fecha_adquisicion: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[TerminalEstado] = mapped_column(
        SAEnum(TerminalEstado, name="terminal_estado"),
        nullable=False,
        default=TerminalEstado.ACTIVO,
    )

    sucursal: Mapped["Sucursal"] = relationship("Sucursal", back_populates="terminales")
