from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.models.usuarios_rol import UsuarioRol
from app.models.restaurante import Restaurante
from app.core.security import hash_password

router = APIRouter(
    prefix="/admin/kiosco",
    tags=["Admin - Kiosco"]
)

async def get_admin_restaurante_id(admin, db: AsyncSession) -> int:
    stmt = select(UsuarioRol.restaurante_id).where(
        UsuarioRol.user_id == admin.id_usuario,
        UsuarioRol.rol_id == 2
    ).limit(1)

    restaurante_id = (await db.execute(stmt)).scalar()

    if not restaurante_id:
        raise HTTPException(
            status_code=403,
            detail="Admin no asociado a restaurante"
        )

    return restaurante_id

@router.get("/usuario")
async def obtener_usuario_kiosco(
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    stmt = (
        select(Usuario)
        .join(UsuarioRol)
        .where(
            UsuarioRol.restaurante_id == restaurante_id,
            UsuarioRol.rol_id == 3  # kiosco
        )
        .limit(1)
    )

    usuario = (await db.execute(stmt)).scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario kiosco no existe")

    restaurante = await db.get(Restaurante, restaurante_id)

    return {
        "id_usuario": usuario.id_usuario,
        "documento": usuario.documento,
        "nombres": usuario.nombres,
        "apellidos": usuario.apellidos,
        "telefono": usuario.telefono,
        "correo": usuario.correo,
        "estado_id": usuario.estado_id,
        "img_restaurante": restaurante.logo if restaurante else None,
    }

@router.patch("/usuario/estado")
async def toggle_estado_usuario_kiosco(
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    stmt = (
        select(Usuario)
        .join(UsuarioRol)
        .where(
            UsuarioRol.restaurante_id == restaurante_id,
            UsuarioRol.rol_id == 3
        )
    )

    usuario = (await db.execute(stmt)).scalar_one_or_none()

    if not usuario:
        raise HTTPException(404, "Usuario kiosco no encontrado")

    usuario.estado_id = 2 if usuario.estado_id == 1 else 1
    usuario.fecha_actualizacion = datetime.utcnow()

    await db.commit()
    await db.refresh(usuario)

    return {
        "id_usuario": usuario.id_usuario,
        "estado_id": usuario.estado_id
    }

@router.patch("/usuario/password")
async def cambiar_password_kiosco(
    password: str = Body(...),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    stmt = (
        select(Usuario)
        .join(UsuarioRol)
        .where(
            UsuarioRol.restaurante_id == restaurante_id,
            UsuarioRol.rol_id == 3
        )
    )

    usuario = (await db.execute(stmt)).scalar_one_or_none()

    if not usuario:
        raise HTTPException(404, "Usuario kiosco no encontrado")

    usuario.contrasena = hash_password(password)
    usuario.fecha_actualizacion = datetime.utcnow()

    await db.commit()

    return {"ok": True}

@router.post("/usuario")
async def crear_usuario_kiosco(
    tipo_documento_id: int = Body(...),
    documento: str = Body(...),
    nombres: str = Body(...),
    apellidos: str = Body(...),
    telefono: str = Body(None),
    correo: str = Body(...),
    contrasena: str = Body(...),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    # validar que no exista ya
    stmt = (
        select(Usuario.id_usuario)
        .join(UsuarioRol)
        .where(
            UsuarioRol.restaurante_id == restaurante_id,
            UsuarioRol.rol_id == 3
        )
    )
    if (await db.execute(stmt)).first():
        raise HTTPException(400, "El usuario del kiosco ya existe")

    usuario = Usuario(
        tipo_documento_id=tipo_documento_id,  # 3 = NIT
        documento=documento,
        nombres=nombres,
        apellidos=apellidos,
        telefono=telefono,
        correo=correo,
        contrasena=hash_password(contrasena),
        estado_id=1,
        fecha_creacion=datetime.utcnow(),
    )

    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)

    rol = UsuarioRol(
        user_id=usuario.id_usuario,
        rol_id=3,  # kiosco
        restaurante_id=restaurante_id
    )

    db.add(rol)
    await db.commit()

    return {"ok": True}
