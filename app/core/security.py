from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.database import get_db
from app.models.usuario import Usuario
from app.models.usuarios_rol import UsuarioRol
from app.models.rol import Rol
from app.schemas.auth import AdminContext, KioscoContext

# =====================================================
# PASSWORDS
# =====================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# =====================================================
# JWT
# =====================================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm="HS256",
    )



async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
        )

        user_id: str | None = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await db.get(Usuario, int(user_id))

    if not user:
        raise credentials_exception

    return user


async def get_admin_user(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminContext:

    stmt = (
        select(
            UsuarioRol.restaurante_id,
            Rol.nombre
        )
        .join(Rol, Rol.id_rol == UsuarioRol.rol_id)
        .where(
            UsuarioRol.user_id == current_user.id_usuario,
            Rol.nombre.in_(["admin_restaurante"])
        )
        .limit(1)
    )

    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene permisos de administrador",
        )

    restaurante_id, rol_nombre = row

    if not restaurante_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrador sin restaurante asignado",
        )

    return AdminContext(
        user_id=current_user.id_usuario,
        restaurante_id=restaurante_id,
        rol=rol_nombre,
    )

async def get_kiosco_context(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> KioscoContext | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
        )
    except JWTError:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    stmt = (
        select(
            UsuarioRol.restaurante_id,
            Rol.nombre
        )
        .join(Rol, Rol.id_rol == UsuarioRol.rol_id)
        .where(
            UsuarioRol.user_id == int(user_id),
            Rol.nombre == "kiosco"
        )
        .limit(1)
    )

    result = await db.execute(stmt)
    row = result.first()

    if not row:
        return None  # 👈 clave

    restaurante_id, rol_nombre = row

    if not restaurante_id:
        return None

    return KioscoContext(
        user_id=int(user_id),
        restaurante_id=restaurante_id,
        rol=rol_nombre,
    )
