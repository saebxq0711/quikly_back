from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.repositories.auth_repo import (
    get_user_by_email, get_user_role, get_user_restaurante_id,
    create_reset_token, get_valid_token, mark_token_used, update_user_password
)
from app.core.email import send_email
from app.core.config import settings

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
    user = await get_user_by_email(db, correo)
    if not user:
        return  # no revelamos si existe o no
    token = await create_reset_token(db, user.id_usuario, ip_creacion)
    link = f"{settings.frontend_url}/reset-password?token={token}"
    await send_email(
        to=user.correo,
        subject="Restablecer contraseña",
        body=f"Hola, haz clic en este link para restablecer tu contraseña: {link}\n\nEste link expira en {settings.reset_token_expire_minutes} minutos."
    )

async def reset_password(db, token: str, new_password: str):
    token_obj = await get_valid_token(db, token)
    if not token_obj:
        raise ValueError("Token inválido, expirado o revocado")

    # 1️⃣ Actualiza la contraseña y el historial en un solo paso
    success = await update_user_password(db, token_obj.usuario_id, new_password)

    # 2️⃣ Marcar token como usado solo si todo fue exitoso
    if success:
        await mark_token_used(db, token_obj)

    return success
