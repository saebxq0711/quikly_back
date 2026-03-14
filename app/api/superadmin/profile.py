from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from app.db.database import get_db
from app.models.usuario import Usuario
from app.models.historial_contrasena import HistorialContrasena
from pydantic import BaseModel, EmailStr, constr
import re
from passlib.hash import bcrypt

router = APIRouter(
    prefix="/superadmin/profile",
    tags=["SuperAdmin Profile"]
)

# -----------------------------
# Pydantic models
# -----------------------------
class ProfileResponse(BaseModel):
    id_usuario: int
    nombres: str
    apellidos: str | None
    correo: str
    telefono: str | None
    estado_id: int


class ProfileUpdateRequest(BaseModel):
    correo: EmailStr
    contrasena: constr(min_length=8)
    confirmar_contrasena: str

    def validate_password(self):
        if self.contrasena != self.confirmar_contrasena:
            raise ValueError("Las contraseñas no coinciden")
        if not re.search(r"[A-Z]", self.contrasena):
            raise ValueError("La contraseña debe tener al menos una mayúscula")
        if not re.search(r"[0-9]", self.contrasena):
            raise ValueError("La contraseña debe tener al menos un número")


# -----------------------------
# Obtener perfil
# -----------------------------
@router.get("/", response_model=ProfileResponse)
async def get_profile(superadmin_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Usuario).where(Usuario.id_usuario == superadmin_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return ProfileResponse(
        id_usuario=user.id_usuario,
        nombres=user.nombres,
        apellidos=user.apellidos,
        correo=user.correo,
        telefono=user.telefono,
        estado_id=user.estado_id,
    )


# -----------------------------
# Actualizar correo y contraseña
# -----------------------------
@router.put("/", response_model=ProfileResponse)
async def update_profile(
    superadmin_id: int,
    payload: ProfileUpdateRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    payload.validate_password()

    # Obtener usuario
    result = await db.execute(
        select(Usuario).where(Usuario.id_usuario == superadmin_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 🔐 Validar contra las últimas 2 contraseñas
    historial_result = await db.execute(
        select(HistorialContrasena)
        .where(HistorialContrasena.usuario_id == superadmin_id)
        .order_by(desc(HistorialContrasena.fecha_creacion))
        .limit(2)
    )
    historial = historial_result.scalars().all()

    for h in historial:
        if bcrypt.verify(payload.contrasena, h.contrasena):
            raise HTTPException(
                status_code=409,
                detail="No puedes reutilizar ninguna de tus últimas 2 contraseñas",
            )

    # 🔑 Hash nueva contraseña
    nueva_contrasena_hash = bcrypt.hash(payload.contrasena)

    # Actualizar usuario
    user.correo = payload.correo
    user.contrasena = nueva_contrasena_hash

    # Guardar en historial
    db.add(
        HistorialContrasena(
            usuario_id=superadmin_id,
            contrasena=nueva_contrasena_hash,
        )
    )

    await db.commit()

    # 🧹 Mantener solo 2 contraseñas en historial
    cleanup_result = await db.execute(
        select(HistorialContrasena)
        .where(HistorialContrasena.usuario_id == superadmin_id)
        .order_by(desc(HistorialContrasena.fecha_creacion))
        .offset(2)
    )
    historiales_antiguos = cleanup_result.scalars().all()

    if historiales_antiguos:
        await db.execute(
            delete(HistorialContrasena).where(
                HistorialContrasena.id_historial_contrasena.in_(
                    [h.id_historial_contrasena for h in historiales_antiguos]
                )
            )
        )
        await db.commit()

    await db.refresh(user)

    return ProfileResponse(
        id_usuario=user.id_usuario,
        nombres=user.nombres,
        apellidos=user.apellidos,
        correo=user.correo,
        telefono=user.telefono,
        estado_id=user.estado_id,
    )
