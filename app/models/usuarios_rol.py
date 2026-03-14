from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class UsuarioRol(Base):
    __tablename__ = "usuarios_rol"

    id_usuario_rol = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    restaurante_id = Column(Integer, ForeignKey("restaurante.id_restaurante"), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    usuario = relationship("Usuario", back_populates="roles_en_restaurantes")
    restaurante = relationship("Restaurante", back_populates="usuarios_rol")
    rol = relationship("Rol", back_populates="usuarios_rol")

