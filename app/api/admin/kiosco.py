from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime

from app.db.database import get_db
from app.core.security import get_current_user, hash_password, verify_password
from app.models.usuario import Usuario
from app.models.usuarios_rol import UsuarioRol
from app.models.restaurante import Restaurante
from app.models.historial_contrasena import HistorialContrasena

router = APIRouter(
    prefix="/admin/kiosco",
    tags=["Admin - Kiosco"]
)

# ---------------------
# Helper: restaurante
# ---------------------
async def get_admin_restaurante_id(admin, db: AsyncSession) -> int:
    stmt = select(UsuarioRol.restaurante_id).where(
        UsuarioRol.user_id == admin.id_usuario,
        UsuarioRol.rol_id == 2
    ).limit(1)

    restaurante_id = (await db.execute(stmt)).scalar()

    if not restaurante_id:
        raise HTTPException(403, "Admin no asociado a restaurante")

    return restaurante_id


# ---------------------
# GET usuario kiosco
# ---------------------
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
            UsuarioRol.rol_id == 3
        )
        .limit(1)
    )

    usuario = (await db.execute(stmt)).scalar_one_or_none()

    if not usuario:
        raise HTTPException(404, "Usuario kiosco no existe")

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


# ---------------------
# Toggle estado
# ---------------------
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


# ---------------------
# Cambiar contraseña
# ---------------------
@router.patch("/usuario/password")
async def cambiar_password_kiosco(
    password: str = Body(...),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # -----------------------------
    # 🧠 validación básica backend
    # -----------------------------
    if not password or len(password.strip()) < 6:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 6 caracteres"
        )

    restaurante_id = await get_admin_restaurante_id(admin, db)

    # 🔒 transacción completa
    async with db.begin():

        # -----------------------------
        # 👤 obtener usuario kiosco
        # -----------------------------
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

        # -----------------------------
        # ❌ misma contraseña actual
        # -----------------------------
        if verify_password(password, usuario.contrasena):
            raise HTTPException(
                status_code=400,
                detail="No puedes usar la misma contraseña actual"
            )

        # -----------------------------
        # 📜 obtener historial (orden sólido)
        # -----------------------------
        stmt_hist = (
            select(HistorialContrasena)
            .where(HistorialContrasena.usuario_id == usuario.id_usuario)
            .order_by(
                HistorialContrasena.fecha_creacion.desc(),
                HistorialContrasena.id_historial_contrasena.desc()
            )
        )

        historial = (await db.execute(stmt_hist)).scalars().all()

        # -----------------------------
        # ❌ validar contra últimas 2
        # -----------------------------
        for h in historial[:2]:
            if verify_password(password, h.contrasena):
                raise HTTPException(
                    status_code=400,
                    detail="No puedes reutilizar las últimas contraseñas"
                )

        # -----------------------------
        # 🧹 mantener máximo 2 (eliminar antes)
        # -----------------------------
        if len(historial) >= 2:
            ids_to_delete = [
                h.id_historial_contrasena for h in historial[1:]
            ]

            await db.execute(
                delete(HistorialContrasena).where(
                    HistorialContrasena.id_historial_contrasena.in_(ids_to_delete)
                )
            )

        # -----------------------------
        # 💾 guardar contraseña actual en historial
        # -----------------------------
        nuevo_historial = HistorialContrasena(
            usuario_id=usuario.id_usuario,
            contrasena=usuario.contrasena,
            fecha_creacion=datetime.utcnow()
        )

        db.add(nuevo_historial)

        # -----------------------------
        # 🔁 actualizar password usuario
        # -----------------------------
        usuario.contrasena = hash_password(password)
        usuario.fecha_actualizacion = datetime.utcnow()

    # 🔥 commit automático por el begin()

    return {"ok": True}


# ---------------------
# Crear usuario kiosco
# ---------------------
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

    hashed = hash_password(contrasena)

    usuario = Usuario(
        tipo_documento_id=tipo_documento_id,
        documento=documento,
        nombres=nombres,
        apellidos=apellidos,
        telefono=telefono,
        correo=correo,
        contrasena=hashed,
        estado_id=1,
        fecha_creacion=datetime.utcnow(),
    )

    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)

    # guardar en historial inicial
    historial = HistorialContrasena(
        usuario_id=usuario.id_usuario,
        contrasena=hashed,
        fecha_creacion=datetime.utcnow()
    )

    db.add(historial)

    rol = UsuarioRol(
        user_id=usuario.id_usuario,
        rol_id=3,
        restaurante_id=restaurante_id
    )

    db.add(rol)
    await db.commit()

    return {"ok": True}