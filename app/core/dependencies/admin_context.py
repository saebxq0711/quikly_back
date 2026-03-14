from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.usuarios_rol import UsuarioRol

class AdminRestauranteContext:
    def __init__(self, user_id: int, restaurante_id: int):
        self.user_id = user_id
        self.restaurante_id = restaurante_id

async def get_admin_restaurante_context(
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminRestauranteContext:

    stmt = select(UsuarioRol.restaurante_id).where(
        UsuarioRol.user_id == admin.id_usuario,
        UsuarioRol.rol_id == 2  # admin restaurante
    )

    restaurante_id = (await db.execute(stmt)).scalar_one_or_none()

    if not restaurante_id:
        raise HTTPException(403, "No es admin de restaurante")

    return AdminRestauranteContext(
        user_id=admin.id_usuario,
        restaurante_id=restaurante_id
    )
