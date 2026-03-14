from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.core.config import settings
from backend.app.models import usuario as models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
SECRET_KEY = settings.secret_key
ALGORITHM = settings.jwt_algorithm

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

        result = await db.execute(select(models.Usuario).filter(models.Usuario.id_usuario == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        # Traemos rol
        rol_result = await db.execute(
            select(models.Roles.nombre)
            .join(models.UsuariosRol, models.UsuariosRol.rol_id == models.Roles.id_rol)
            .filter(models.UsuariosRol.user_id == user.id_usuario)
        )
        rol = rol_result.scalar_one_or_none()

        return {
            "id_usuario": user.id_usuario,
            "nombres": user.nombres,
            "apellidos": user.apellidos,
            "correo": user.correo,
            "rol": rol if rol else None
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
