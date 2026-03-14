# app/api/admin/perfil.py

from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from passlib.context import CryptContext
import os
import uuid

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.usuario import Usuario
from app.models.restaurante import Restaurante
from app.models.usuarios_rol import UsuarioRol
from app.models.historial_contrasena import HistorialContrasena

router = APIRouter(
    prefix="/admin/perfil",
    tags=["Admin - Perfil"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.put("/contrasena")
async def cambiar_contrasena(
    contrasena_actual: str = Body(..., embed=True),
    nueva_contrasena: str = Body(..., embed=True),
    confirmar_contrasena: str = Body(..., embed=True),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if nueva_contrasena != confirmar_contrasena:
        raise HTTPException(400, "Las contraseñas no coinciden")

    if len(nueva_contrasena) < 8:
        raise HTTPException(400, "La contraseña debe tener al menos 8 caracteres")

    stmt = select(Usuario).where(Usuario.id_usuario == admin.id_usuario)
    usuario = (await db.execute(stmt)).scalar_one()

    if not pwd_context.verify(contrasena_actual, usuario.contrasena):
        raise HTTPException(401, "Contraseña actual incorrecta")

    usuario.contrasena = pwd_context.hash(nueva_contrasena)

    await db.commit()

    return {"ok": True, "message": "Contraseña actualizada correctamente"}



UPLOAD_DIR = "uploads/logos"


@router.put("/logo")
async def cambiar_logo_restaurante(
    logo: UploadFile = File(...),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1️⃣ obtener restaurante del admin
    stmt = select(UsuarioRol.restaurante_id).where(
        UsuarioRol.user_id == admin.id_usuario,
        UsuarioRol.rol_id == 2
    )
    restaurante_id = (await db.execute(stmt)).scalar()

    if not restaurante_id:
        raise HTTPException(403, "Admin no asociado a restaurante")

    # 2️⃣ validar archivo
    if logo.content_type not in ["image/png", "image/jpeg", "image/webp"]:
        raise HTTPException(400, "Formato de imagen no permitido")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = f"{uuid.uuid4().hex}_{logo.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # 3️⃣ guardar archivo
    with open(filepath, "wb") as f:
        f.write(await logo.read())

    # 4️⃣ actualizar restaurante
    stmt = select(Restaurante).where(Restaurante.id_restaurante == restaurante_id)
    restaurante = (await db.execute(stmt)).scalar_one()

    restaurante.logo = f"/{UPLOAD_DIR}/{filename}"

    await db.commit()
    await db.refresh(restaurante)

    return {
        "ok": True,
        "logo": restaurante.logo
    }

@router.get("")
async def obtener_perfil_admin(
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            Usuario.nombres,
            Usuario.apellidos,
            Usuario.correo,
            Usuario.telefono,
            Restaurante.nombre,
            Restaurante.logo
        )
        .join(UsuarioRol, UsuarioRol.user_id == Usuario.id_usuario)
        .join(Restaurante, Restaurante.id_restaurante == UsuarioRol.restaurante_id)
        .where(
            Usuario.id_usuario == admin.id_usuario,
            UsuarioRol.rol_id == 2
        )
    )

    result = (await db.execute(stmt)).first()

    if not result:
        raise HTTPException(404, "Perfil no encontrado")

    return {
        "usuario": {
            "nombres": result.nombres,
            "apellidos": result.apellidos,
            "correo": result.correo,
            "telefono": result.telefono,
        },
        "restaurante": {
            "nombre": result.nombre,
            "logo": result.logo,
        }
    }

@router.put("/contrasena")
async def cambiar_contrasena(
    contrasena_actual: str = Body(..., embed=True),
    nueva_contrasena: str = Body(..., embed=True),
    confirmar_contrasena: str = Body(..., embed=True),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if nueva_contrasena != confirmar_contrasena:
        raise HTTPException(400, "Las contraseñas no coinciden")
    if len(nueva_contrasena) < 8:
        raise HTTPException(400, "La contraseña debe tener al menos 8 caracteres")

    # obtener usuario
    stmt = select(Usuario).where(Usuario.id_usuario == admin.id_usuario)
    usuario = (await db.execute(stmt)).scalar_one()

    if not pwd_context.verify(contrasena_actual, usuario.contrasena):
        raise HTTPException(401, "Contraseña actual incorrecta")

    # ✅ Validar historial (últimas 2)
    stmt_hist = (
        select(HistorialContrasena.contrasena)
        .where(HistorialContrasena.usuario_id == usuario.id_usuario)
        .order_by(desc(HistorialContrasena.fecha_creacion))
        .limit(2)
    )
    ultimas = (await db.execute(stmt_hist)).scalars().all()

    for h in ultimas:
        if pwd_context.verify(nueva_contrasena, h):
            raise HTTPException(
                400,
                "No puedes reutilizar las últimas 2 contraseñas"
            )

    # ✅ Guardar contraseña actual en historial
    historial = HistorialContrasena(
        usuario_id=usuario.id_usuario,
        contrasena=usuario.contrasena
    )
    db.add(historial)

    # ✅ Actualizar usuario
    usuario.contrasena = pwd_context.hash(nueva_contrasena)

    await db.commit()

    # ✅ Mantener solo últimas 2
    stmt_delete = (
        select(HistorialContrasena)
        .where(HistorialContrasena.usuario_id == usuario.id_usuario)
        .order_by(desc(HistorialContrasena.fecha_creacion))
    )
    historial_total = (await db.execute(stmt_delete)).scalars().all()
    if len(historial_total) > 2:
        for h in historial_total[2:]:
            await db.delete(h)
        await db.commit()

    return {"ok": True, "message": "Contraseña actualizada correctamente"}