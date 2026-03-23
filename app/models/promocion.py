from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Time,
    Date,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Promocion(Base):
    __tablename__ = "promocion"

    id_promocion = Column(Integer, primary_key=True, index=True)
    restaurante_id = Column(Integer, ForeignKey("restaurante.id_restaurante"), nullable=False)

    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    img_flyer = Column(String, nullable=True)
    img_flyer_path = Column(String, nullable=True)

    # "1,2,3,4,5"
    dias_semana = Column(String, nullable=True)

    hora_inicio = Column(Time, nullable=True)
    hora_fin = Column(Time, nullable=True)

    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)

    estado_id = Column(Integer, default=1)

    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # 🔗 Relaciones
    productos = relationship(
        "PromocionProducto",
        back_populates="promocion",
        cascade="all, delete-orphan",
    )
