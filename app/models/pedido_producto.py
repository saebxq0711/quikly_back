# app/models/pedido_producto.py
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.database import Base

class PedidoProducto(Base):
    __tablename__ = "pedido_producto"

    id_pedido_producto = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id_pedido"), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("producto.id_producto"), nullable=True, index=True)
    nombre_producto = Column(String(150), nullable=False)
    precio_base = Column(Numeric(10, 2), nullable=False)
    cantidad = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    # Relaciones
    pedido = relationship("Pedido", back_populates="productos")
    producto = relationship("Producto")

# Import tardío para evitar errores de inicialización
from app.models.pedido_producto_opcion import PedidoProductoOpcion

PedidoProducto.opciones = relationship(
    "PedidoProductoOpcion",
    back_populates="pedido_producto",
    cascade="all, delete-orphan"
)
