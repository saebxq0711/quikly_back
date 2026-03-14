from sqlalchemy import select, insert
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.usuarios_rol import UsuarioRol
from app.models.token_contrasena import TokenContrasena
from app.models.historial_contrasena import HistorialContrasena
from passlib.context import CryptContext
from datetime import datetime, timedelta
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Usuarios ---
async def get_user_by_email(db, correo: str):
    stmt = select(Usuario).where(Usuario.correo == correo)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_user_role(db, user_id: int):
    stmt = (
        select(Rol.nombre)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id_rol)
        .where(UsuarioRol.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar()

async def get_user_restaurante_id(db, user_id: int):
    stmt = (
        select(UsuarioRol.restaurante_id)
        .where(UsuarioRol.user_id == user_id)
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# --- Tokens recuperación ---
async def create_reset_token(db, user_id: int, ip_creacion: str = None):
    token = str(uuid.uuid4())
    now = datetime.utcnow()
    expire = now + timedelta(minutes=30)

    token_obj = TokenContrasena(
        usuario_id=user_id,
        token=token,
        fecha_creacion=now,
        fecha_expiracion=expire,
        ip_creacion=ip_creacion,
        revocado=False
    )
    db.add(token_obj)
    await db.commit()
    return token

async def get_valid_token(db, token: str):
    now = datetime.utcnow()
    stmt = select(TokenContrasena).where(
        TokenContrasena.token == token,
        TokenContrasena.fecha_expiracion > now,
        TokenContrasena.fecha_uso == None,
        TokenContrasena.revocado == False
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def mark_token_used(db, token_obj):
    token_obj.fecha_uso = datetime.utcnow()
    db.add(token_obj)
    await db.commit()

MAX_HISTORY = 3

async def update_user_password(db, user_id: int, new_password: str):
    user = await db.get(Usuario, user_id)
    if not user:
        return False

    stmt = select(HistorialContrasena).where(
        HistorialContrasena.usuario_id == user_id
    ).order_by(HistorialContrasena.fecha_creacion.desc())

    result = await db.execute(stmt)
    old_entries = result.scalars().all()

    for entry in old_entries:
        if pwd_context.verify(new_password, entry.contrasena):
            raise ValueError("No puedes usar una contraseña anterior")

    hashed_password = pwd_context.hash(new_password)

    await db.execute(
        insert(HistorialContrasena).values(
            usuario_id=user.id_usuario,
            contrasena=hashed_password,
            fecha_creacion=datetime.utcnow()
        )
    )

    if len(old_entries) >= MAX_HISTORY:
        for entry in old_entries[MAX_HISTORY - 1:]:
            await db.delete(entry)

    user.contrasena = hashed_password
    db.add(user)
    await db.commit()
    return True
