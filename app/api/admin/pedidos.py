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
from app.models.usuarios_rol import UsuarioRol
from app.schemas.pedido import PedidoSchema

router = APIRouter(prefix="/admin/pedidos", tags=["Pedidos Admin"])


# =========================
# CONFIG ESTADOS (según tu BD)
# =========================

ESTADOS = {
    4: "aprobado",
    5: "pendiente",
    6: "rechazado",
    7: "entregado",
}

# Reglas de transición
TRANSICIONES_VALIDAS = {
    5: [4, 6],  # pendiente → aprobado / rechazado
    4: [7],     # aprobado → entregado
    6: [],      # rechazado → final
    7: [],      # entregado → final
}


# =========================
# SCHEMAS
# =========================

class CambiarEstadoRequest(BaseModel):
    estado_id: int


# =========================
# HELPERS (reutilizables)
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
        selectinload(Pedido.productos).selectinload(PedidoProducto.opciones)
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
        raise HTTPException(
            status_code=400,
            detail=f"Estado actual inválido: {estado_actual}"
        )

    if nuevo_estado not in TRANSICIONES_VALIDAS[estado_actual]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cambiar de '{ESTADOS.get(estado_actual)}' a '{ESTADOS.get(nuevo_estado)}'"
        )


# =========================
# ENDPOINTS
# =========================

@router.get("/", response_model=List[PedidoSchema])
async def listar_pedidos(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    restaurante_id = await get_restaurante_id(current_user, db)

    stmt = select(Pedido).options(
        selectinload(Pedido.productos).selectinload(PedidoProducto.opciones)
    ).where(Pedido.restaurante_id == restaurante_id)

    result = await db.execute(stmt)
    pedidos = result.scalars().unique().all()

    return pedidos


@router.patch("/{pedido_id}/estado")
async def cambiar_estado_pedido(
    pedido_id: int,
    body: CambiarEstadoRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_restaurante_id(current_user, db)

    pedido = await get_pedido_or_404(pedido_id, restaurante_id, db)

    estado_actual = pedido.estado_id

    # Validar transición
    validar_transicion(estado_actual, body.estado_id)

    # Actualizar estado
    pedido.estado_id = body.estado_id
    db.add(pedido)

    await db.commit()
    await db.refresh(pedido)

    return {
        "msg": f"Estado cambiado de '{ESTADOS.get(estado_actual)}' a '{ESTADOS.get(body.estado_id)}'",
        "pedido": pedido
    }


# =========================
# OPCIONAL: listar estados
# =========================

@router.get("/estados")
async def listar_estados():
    return [
        {"id_estado": k, "nombre": v}
        for k, v in ESTADOS.items()
    ]