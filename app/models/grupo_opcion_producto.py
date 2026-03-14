# app/models/grupo_opcion_producto.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class GrupoOpcionProducto(Base):
    __tablename__ = "grupo_opcion_producto"

    id_grupo_opcion = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("producto.id_producto"))
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # tamaño | topping
    obligatorio = Column(Boolean, default=False)
    min_selecciones = Column(Integer, default=0)
    max_selecciones = Column(Integer, default=1)
    estado_id = Column(Integer, default=1)

    producto = relationship("Producto", back_populates="grupos_opcion")
    opciones = relationship(
        "OpcionProducto",
        back_populates="grupo",
        cascade="all, delete-orphan"
    )
