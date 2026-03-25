# app/routers/admin_pedidos.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from pydantic import BaseModel

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.pedido import Pedido
from app.models.pedido_producto import PedidoProducto
from app.models.producto import Producto
from app.models.usuarios_rol import UsuarioRol
from app.schemas.pedido import PedidoSchema
from app.services.storage_service import get_public_url

router = APIRouter(prefix="/admin/pedidos", tags=["Pedidos Admin"])

# =========================
# CONFIG ESTADOS
# =========================

ESTADOS = {
    4: "aprobado",
    5: "pendiente",
    6: "rechazado",
    7: "entregado",
}

TRANSICIONES_VALIDAS = {
    5: [4, 6],
    4: [7],
    6: [],
    7: [],
}

# =========================
# SCHEMAS
# =========================

class CambiarEstadoRequest(BaseModel):
    estado_id: int

# =========================
# HELPERS
# =========================

async def get_restaurante_id(current_user, db: AsyncSession) -> int:
    stmt = select(UsuarioRol.restaurante_id).where(
        UsuarioRol.user_id == current_user.id_usuario,
        UsuarioRol.rol_id == 2
    ).limit(1)

    restaurante_id = (await db.execute(stmt)).scalar()

    if not restaurante_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no asociado a un restaurante"
        )

    return restaurante_id


async def get_pedido_or_404(pedido_id: int, restaurante_id: int, db: AsyncSession) -> Pedido:
    stmt = select(Pedido).options(
        selectinload(Pedido.productos)
        .selectinload(PedidoProducto.opciones),
        selectinload(Pedido.productos)
        .selectinload(PedidoProducto.producto)  # 🔥 clave para imagen
    ).where(
        Pedido.id_pedido == pedido_id,
        Pedido.restaurante_id == restaurante_id
    )

    pedido = (await db.execute(stmt)).scalar_one_or_none()

    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )

    return pedido


def validar_transicion(estado_actual: int, nuevo_estado: int):
    if estado_actual not in TRANSICIONES_VALIDAS:
        raise HTTPException(status_code=400, detail="Estado inválido")

    if nuevo_estado not in TRANSICIONES_VALIDAS[estado_actual]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cambiar de '{ESTADOS.get(estado_actual)}' a '{ESTADOS.get(nuevo_estado)}'"
        )

# =========================
# SERIALIZER (🔥 CLAVE)
# =========================

def serialize_pedido(pedido: Pedido):
    return {
        "id_pedido": pedido.id_pedido,
        "cliente_identificacion": pedido.cliente_identificacion,
        "cliente_nombres": pedido.cliente_nombres,
        "cliente_correo": pedido.cliente_correo,
        "cliente_telefono": pedido.cliente_telefono,
        "estado_id": pedido.estado_id,
        "total": float(pedido.total),
        "fecha_creacion": pedido.fecha_creacion,
        "productos": [
            {
                "id_pedido_producto": prod.id_pedido_producto,
                "nombre_producto": prod.nombre_producto,
                "cantidad": prod.cantidad,
                "precio_base": float(prod.precio_base),
                "subtotal": float(prod.subtotal),
                "imagen_url": (
                    get_public_url(prod.producto.img_producto)
                    if prod.producto and prod.producto.img_producto
                    else None
                ),
                "opciones": [
                    {
                        "tipo_opcion": o.tipo_opcion,
                        "nombre_opcion": o.nombre_opcion,
                        "precio_adicional": float(o.precio_adicional),
                    }
                    for o in prod.opciones
                ],
            }
            for prod in pedido.productos
        ],
    }

# =========================
# ENDPOINTS
# =========================

# 🔹 LISTAR
@router.get("/")
async def listar_pedidos(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_restaurante_id(current_user, db)

    stmt = select(Pedido).options(
        selectinload(Pedido.productos)
        .selectinload(PedidoProducto.opciones),
        selectinload(Pedido.productos)
        .selectinload(PedidoProducto.producto)
    ).where(Pedido.restaurante_id == restaurante_id)

    result = await db.execute(stmt)
    pedidos = result.scalars().unique().all()

    return [serialize_pedido(p) for p in pedidos]


# 🔹 DETALLE (🔥 PARA BOTÓN VER)
@router.get("/{pedido_id}")
async def obtener_pedido(
    pedido_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_restaurante_id(current_user, db)

    pedido = await get_pedido_or_404(pedido_id, restaurante_id, db)

    return serialize_pedido(pedido)


# 🔹 CAMBIAR ESTADO
@router.patch("/{pedido_id}/estado")
async def cambiar_estado_pedido(
    pedido_id: int,
    body: CambiarEstadoRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_restaurante_id(current_user, db)

    pedido = await get_pedido_or_404(pedido_id, restaurante_id, db)

    validar_transicion(pedido.estado_id, body.estado_id)

    pedido.estado_id = body.estado_id
    db.add(pedido)

    await db.commit()
    await db.refresh(pedido)

    return {"msg": "Estado actualizado correctamente"}


# 🔹 ESTADOS
@router.get("/estados")
async def listar_estados():
    return [
        {"id_estado": k, "nombre": v}
        for k, v in ESTADOS.items()
    ]