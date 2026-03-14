# app/models/opcion_producto.py
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.database import Base

class OpcionProducto(Base):
    __tablename__ = "opcion_producto"

    id_opcion_producto = Column(Integer, primary_key=True, index=True)
    grupo_opcion_id = Column(Integer, ForeignKey("grupo_opcion_producto.id_grupo_opcion"))
    nombre = Column(String, nullable=False)
    precio_adicional = Column(Numeric(10, 2), default=0)
    estado_id = Column(Integer, default=1)

    grupo = relationship("GrupoOpcionProducto", back_populates="opciones")
