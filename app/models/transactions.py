from datetime import date
from decimal import Decimal
from sqlalchemy import Integer, ForeignKey, Date, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class TransaccionMensual(Base):
    __tablename__ = "transacciones_mensual"
    __table_args__ = (
        Index("ix_trans_terminal_periodo", "terminal_id", "periodo"),
        Index("ix_trans_sucursal_periodo", "sucursal_id", "periodo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(ForeignKey("terminales.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), nullable=False)
    periodo: Mapped[date] = mapped_column(Date, nullable=False)  # first day of month
    monto_total_mm: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    num_transacciones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
