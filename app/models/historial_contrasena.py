from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.db.database import Base

class HistorialContrasena(Base):
    __tablename__ = "historial_contrasena"

    id_historial_contrasena = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    contrasena = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
