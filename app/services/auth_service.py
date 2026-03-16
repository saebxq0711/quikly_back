# auth_service.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.repositories.auth_repo import (
    get_user_by_email, get_user_role, get_user_restaurante_id,
    create_reset_token, get_valid_token, mark_token_used, update_user_password
)
from app.core.config import settings
from app.services.email_service import send_reset_password_email as resend_send_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Autenticación existente ---
async def authenticate(db, correo, contrasena):
    from app.core.security import verify_password

    user = await get_user_by_email(db, correo)
    if not user:
        return None

    if not verify_password(contrasena, user.contrasena):
        return None

    rol = await get_user_role(db, user.id_usuario)
    restaurante_id = await get_user_restaurante_id(db, user.id_usuario)

    return {
        "id_usuario": user.id_usuario,
        "rol": rol.lower().replace(" ", "_") if rol else None,
        "restaurante_id": restaurante_id
    }

# --- Flujo reset password ---
async def send_reset_password_email(db, correo: str, ip_creacion: str = None):
    """
    Envía correo de restablecimiento de contraseña usando Resend.
    No revela si el usuario existe.
    """
    user = await get_user_by_email(db, correo)
    if not user:
        return  # no revelamos si existe o no

    # Crear token en DB
    token = await create_reset_token(db, user.id_usuario, ip_creacion)

    # Link de reset
    link = f"{settings.frontend_url}/reset-password?token={token}"

    # 🚀 Enviar correo vía Resend
    await resend_send_email(user.correo, token)


async def reset_password(db, token: str, new_password: str):
    """
    Resetea la contraseña del usuario usando el token.
    """
    token_obj = await get_valid_token(db, token)
    if not token_obj:
        raise ValueError("Token inválido, expirado o revocado")

    # 1️⃣ Actualiza la contraseña y el historial en un solo paso
    success = await update_user_password(db, token_obj.usuario_id, new_password)

    # 2️⃣ Marcar token como usado solo si todo fue exitoso
    if success:
        await mark_token_used(db, token_obj)

    return success