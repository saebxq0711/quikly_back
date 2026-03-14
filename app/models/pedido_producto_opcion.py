# app/models/pedido_producto_opcion.py
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.database import Base

class PedidoProductoOpcion(Base):
    __tablename__ = "pedido_producto_opcion"

    id_pedido_producto_opcion = Column(Integer, primary_key=True, index=True)
    pedido_producto_id = Column(Integer, ForeignKey("pedido_producto.id_pedido_producto"), nullable=False)
    tipo_opcion = Column(String(50), nullable=False)
    nombre_opcion = Column(String(100), nullable=False)
    precio_adicional = Column(Float, nullable=False)

    # Relaciones
    pedido_producto = relationship("PedidoProducto", back_populates="opciones")
