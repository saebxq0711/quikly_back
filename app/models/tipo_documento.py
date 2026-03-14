from sqlalchemy import Column, Integer, String
from app.db.database import Base

class TipoDocumento(Base):
    __tablename__ = "tipo_documento"

    id_tipo_documento = Column(Integer, primary_key=True)
    nombre = Column(String(20), nullable=False)
    siigo_code = Column(String(10), nullable=True)