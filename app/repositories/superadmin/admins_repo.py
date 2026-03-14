from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.usuario import Usuario
from app.models.usuarios_rol import UsuarioRol

class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_admin(self, nombres: str, apellidos: str, correo: str, telefono: str, contrasena: str, restaurante_id: int | None = None) -> Usuario:
        # 1️⃣ Crear usuario
        nuevo = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            telefono=telefono,
            contrasena=contrasena,  # 🔒 ideal: hashear antes de guardar
            estado_id=1
        )
        self.db.add(nuevo)
        await self.db.commit()
        await self.db.refresh(nuevo)

        # 2️⃣ Asignar rol administrador
        rol = UsuarioRol(
            user_id=nuevo.id_usuario,
            rol_id=2,  # Administrador
            restaurante_id=restaurante_id if restaurante_id != 0 else None
        )
        self.db.add(rol)
        await self.db.commit()

        return nuevo

    async def get_by_email(self, correo: str) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.correo == correo))
        return result.scalars().first()
