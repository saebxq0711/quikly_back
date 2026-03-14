from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from app.db.base import Base
from datetime import datetime

class TokenContrasena(Base):
    __tablename__ = "token_contrasena"
    id_token_contrasena = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_uso = Column(DateTime, nullable=True)
    fecha_expiracion = Column(DateTime, nullable=False)
    ip_creacion = Column(String(45), nullable=True)
    revocado = Column(Boolean, default=False)
