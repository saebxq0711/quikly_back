from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from app.db.database import Base
from sqlalchemy.orm import relationship

class Producto(Base):
    __tablename__ = "producto"

    id_producto = Column(Integer, primary_key=True, index=True)
    restaurante_id = Column(Integer, ForeignKey("restaurante.id_restaurante"))
    categoria_id = Column(Integer, ForeignKey("categoria.id_categoria"))
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    precio_base = Column(Numeric(10, 2), nullable=False)
    img_producto = Column(String, nullable=True)
    estado_id = Column(Integer, default=1)

    categoria = relationship(
        "Categoria",
        back_populates="productos"
    )
    
    grupos_opcion = relationship(
        "GrupoOpcionProducto",
        back_populates="producto",
        cascade="all, delete-orphan"
    )