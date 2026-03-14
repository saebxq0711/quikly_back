from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Restaurante(Base):
    __tablename__ = "restaurante"

    id_restaurante = Column(Integer, primary_key=True, index=True)
    nit = Column(BigInteger, nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    logo = Column(String(255), nullable=True)
    color_primario = Column(String(7), nullable=True)
    color_secundario = Column(String(7), nullable=True)
    estado_id = Column(Integer, default=1)  # 1 = activo, 2 = inactivo, 3 = eliminado
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con usuarios_rol
    usuarios_rol = relationship("UsuarioRol", back_populates="restaurante")
    # Restaurante
    
