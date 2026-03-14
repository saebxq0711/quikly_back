from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.integrations.bancolombia.qr_service import generate_qr

from app.models.pedido import Pedido
from app.models.pedido_producto import PedidoProducto
from app.models.pedido_producto_opcion import PedidoProductoOpcion
from app.models.tipo_documento import TipoDocumento

router = APIRouter(
    prefix="/kiosco/codigo-qr",
    tags=["Kiosco QR"]
)

# =========================
# Schemas
# =========================

class Opcion(BaseModel):
    tipo_opcion: Optional[str] = None
    nombre_opcion: str
    precio_adicional: float = 0


class CartItem(BaseModel):
    producto_id: int
    nombre: str
    precio: float
    cantidad: int
    seleccion: Optional[List[Opcion]] = []


class Customer(BaseModel):
    documentType: str
    documentNumber: str
    name: str
    email: str
    phone: str


class PedidoRequest(BaseModel):
    restaurante_id: int
    customer: Customer
    cart: List[CartItem]


# =========================
# Endpoint
# =========================

@router.post("/generate-qr")
async def create_order_and_generate_qr(
    payload: PedidoRequest,
    db: AsyncSession = Depends(get_db)
):

    if not payload.cart:
        raise HTTPException(400, "El carrito está vacío")

    # =========================
    # Buscar tipo documento
    # =========================

    stmt = select(TipoDocumento).where(
        TipoDocumento.nombre == payload.customer.documentType
    )

    result = await db.execute(stmt)
    tipo_doc = result.scalar_one_or_none()

    if not tipo_doc:
        raise HTTPException(400, "Tipo de documento inválido")

    total = 0

    try:

        # =========================
        # Crear pedido
        # =========================

        pedido = Pedido(
            restaurante_id=payload.restaurante_id,
            tipo_documento_id=tipo_doc.id_tipo_documento,
            cliente_identificacion=payload.customer.documentNumber,
            cliente_nombres=payload.customer.name,
            cliente_correo=payload.customer.email,
            cliente_telefono=payload.customer.phone,
            estado_id=5,
            total=0
        )

        db.add(pedido)
        await db.flush()

        # =========================
        # Crear productos
        # =========================

        for item in payload.cart:

            extras_total = sum(
                op.precio_adicional for op in (item.seleccion or [])
            )

            subtotal = (item.precio + extras_total) * item.cantidad

            pedido_producto = PedidoProducto(
                pedido_id=pedido.id_pedido,
                producto_id=item.producto_id,
                nombre_producto=item.nombre,
                precio_base=item.precio,
                cantidad=item.cantidad,
                subtotal=subtotal
            )

            db.add(pedido_producto)
            await db.flush()

            for op in item.seleccion or []:

                opcion = PedidoProductoOpcion(
                    pedido_producto_id=pedido_producto.id_pedido_producto,
                    tipo_opcion=op.tipo_opcion or "opcion",
                    nombre_opcion=op.nombre_opcion,
                    precio_adicional=op.precio_adicional
                )

                db.add(opcion)

            total += subtotal

        pedido.total = total

        # =========================
        # Generar QR
        # =========================

        qr = await generate_qr(
            payload.customer.model_dump(),
            int(total)
        )

        pedido.qr_reference = qr.get("qr_id")

        await db.commit()

        return {
            "pedido_id": pedido.id_pedido,
            "qr_id": qr.get("qr_id"),
            "qr_image": qr.get("qr_image"),
            "total": total
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            500,
            f"Error creando pedido: {str(e)}"
        )