# app/models/pedido.py

from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Pedido(Base):
    __tablename__ = "pedido"

    id_pedido = Column(Integer, primary_key=True, index=True)

    restaurante_id = Column(
        Integer,
        ForeignKey("restaurante.id_restaurante"),
        nullable=False
    )

    tipo_documento_id = Column(
        Integer,
        ForeignKey("tipo_documento.id_tipo_documento"),
        nullable=True
    )

    cliente_identificacion = Column(String(50), nullable=True)
    cliente_nombres = Column(String(150), nullable=True)
    cliente_correo = Column(String(150), nullable=True)
    cliente_telefono = Column(String(50), nullable=True)

    estado_id = Column(Integer, nullable=False, default=5)

    total = Column(Numeric(10, 2), nullable=False)

    qr_reference = Column(String(120))
    qr_payload = Column(JSON)

    transaccion_banco = Column(String(120))
    siigo_invoice_id = Column(String(120))

    # Fechas con zona horaria (TIMESTAMPTZ en PostgreSQL)

    fecha_creacion = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    fecha_pago = Column(
        DateTime(timezone=True),
        nullable=True
    )

    fecha_facturacion = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relaciones

    restaurante = relationship(
        "Restaurante",
        backref="pedidos"
    )

    productos = relationship(
        "PedidoProducto",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )