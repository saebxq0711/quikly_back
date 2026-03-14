from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base
from sqlalchemy.orm import relationship

class Categoria(Base):
    __tablename__ = "categoria"

    id_categoria = Column(Integer, primary_key=True, index=True)
    restaurante_id = Column(Integer, ForeignKey("restaurante.id_restaurante"))
    nombre = Column(String, nullable=False)
    img_categoria = Column(String, nullable=True)
    orden = Column(Integer, default=0)
    estado_id = Column(Integer, default=1)

    productos = relationship(
        "Producto",
        back_populates="categoria",
        lazy="selectin"
    )