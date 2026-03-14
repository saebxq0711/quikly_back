from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from enum import Enum


class PromocionProducto(Base):
    __tablename__ = "promocion_producto"

    id_promocion_producto = Column(Integer, primary_key=True, index=True)

    promocion_id = Column(
        Integer,
        ForeignKey("promocion.id_promocion", ondelete="CASCADE"),
        nullable=False,
    )

    producto_id = Column(
        Integer,
        ForeignKey("producto.id_producto"),
        nullable=False,
    )

    # OJO: debe coincidir con el CHECK de la DB
    tipo_descuento = Column(String, nullable=False)  # "Porcentaje" | "Monto"
    valor_descuento = Column(Float, nullable=False)

    fecha_creacion = Column(DateTime, server_default=func.now())

    # 🔗 Relaciones
    promocion = relationship("Promocion", back_populates="productos")
    producto = relationship("Producto")


class TipoDescuento(str, Enum):
    PORCENTAJE = "Porcentaje"
    MONTO = "Monto"