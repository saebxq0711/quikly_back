from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    tipo_documento_id = Column(Integer, nullable=False)  # <-- agregado
    documento = Column(String(20), nullable=False)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=True)       # <-- agregado
    telefono = Column(String(50), nullable=True)         # <-- agregado
    correo = Column(String(100), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    estado_id = Column(Integer, default=1)              # <-- agregado si lo usas
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con usuarios_rol
    roles_en_restaurantes = relationship("UsuarioRol", back_populates="usuario")
