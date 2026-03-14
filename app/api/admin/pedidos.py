# app/routers/admin_pedidos.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.pedido import Pedido
from app.models.pedido_producto import PedidoProducto
from app.models.usuarios_rol import UsuarioRol
from app.schemas.pedido import PedidoSchema  # <- importamos el schema

router = APIRouter(prefix="/admin/pedidos", tags=["Pedidos Admin"])


@router.get("/", response_model=List[PedidoSchema])
async def listar_pedidos(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 🔹 Buscar el restaurante del admin
    stmt_rest = select(UsuarioRol.restaurante_id).where(
        UsuarioRol.user_id == current_user.id_usuario,
        UsuarioRol.rol_id == 2
    ).limit(1)
    restaurante_id = (await db.execute(stmt_rest)).scalar()

    if not restaurante_id:
        raise HTTPException(status_code=403, detail="Usuario no asociado a un restaurante")

    # 🔹 Cargar pedidos con productos y opciones
    stmt_pedidos = select(Pedido).options(
        selectinload(Pedido.productos).selectinload(PedidoProducto.opciones)
    ).where(Pedido.restaurante_id == restaurante_id)

    result = await db.execute(stmt_pedidos)
    pedidos = result.scalars().unique().all()

    return pedidos  # Pydantic schema convierte automáticamente a JSON


@router.post("/{pedido_id}/entregado")
async def marcar_entregado(
    pedido_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verificar que el usuario admin pertenezca al restaurante del pedido
    stmt_rest = select(UsuarioRol.restaurante_id).where(
        UsuarioRol.user_id == current_user.id_usuario,
        UsuarioRol.rol_id == 2
    ).limit(1)
    restaurante_id = (await db.execute(stmt_rest)).scalar()
    if not restaurante_id:
        raise HTTPException(status_code=403, detail="Usuario no asociado a un restaurante")

    # Obtener el pedido
    stmt_pedido = select(Pedido).where(
        Pedido.id_pedido == pedido_id,
        Pedido.restaurante_id == restaurante_id
    )
    pedido = (await db.execute(stmt_pedido)).scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # Cambiar estado a entregado (7)
    pedido.estado_id = 7
    db.add(pedido)
    await db.commit()
    await db.refresh(pedido)

    return {"msg": "Pedido marcado como entregado", "pedido": pedido}