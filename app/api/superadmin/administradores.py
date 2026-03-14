from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.db.database import get_db
from app.models.usuario import Usuario
from app.models.usuarios_rol import UsuarioRol
from app.models.restaurante import Restaurante
from app.schemas.restaurante import RestauranteOut

router = APIRouter(
    prefix="/superadmin/administradores",
    tags=["SuperAdmin Administradores"]
)

# ================================
# Pydantic Schemas
# ================================
class AdminBase(BaseModel):
    nombres: str
    apellidos: str
    correo: EmailStr
    telefono: str
    restaurante_id: Optional[int] = None

class AdminCreate(AdminBase):
    contrasena: str
    tipo_documento_id: Optional[int] = None
    documento: Optional[str] = None

class AdminOut(AdminBase):
    id_usuario: int
    estado_id: int
    restaurante: Optional[str]

class EstadoUpdate(BaseModel):
    estado: int

# ================================
# LISTAR ADMINISTRADORES
# ================================
@router.get("/", response_model=dict)
async def list_admins(
    search: Optional[str] = None,
    estado: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit

    stmt = (
        select(
            Usuario.id_usuario,
            Usuario.nombres,
            Usuario.apellidos,
            Usuario.correo,
            Usuario.telefono,
            Usuario.estado_id,
            Restaurante.nombre.label("restaurante")
        )
        .join(UsuarioRol, Usuario.id_usuario == UsuarioRol.user_id)
        .outerjoin(Restaurante, Restaurante.id_restaurante == UsuarioRol.restaurante_id)
        .where(UsuarioRol.rol_id == 2)
    )

    if search:
        stmt = stmt.where(
            or_(
                Usuario.nombres.ilike(f"%{search}%"),
                Usuario.apellidos.ilike(f"%{search}%"),
                Usuario.correo.ilike(f"%{search}%"),
                Usuario.telefono.ilike(f"%{search}%"),
            )
        )

    if estado is not None:
        stmt = stmt.where(Usuario.estado_id == estado)

    stmt = stmt.order_by(Usuario.id_usuario.desc())

    total_query = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_query)).scalar() or 0
    total_pages = (total + limit - 1) // limit

    result = await db.execute(stmt.offset(offset).limit(limit))
    items = [dict(row._mapping) for row in result]

    return {"items": items, "total_pages": total_pages}

# ================================
# CAMBIAR ESTADO
# ================================
@router.patch("/{admin_id}/estado", response_model=dict)
async def update_admin_estado(
    admin_id: int,
    payload: EstadoUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Usuario).where(Usuario.id_usuario == admin_id))
    usuario = result.scalars().first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")

    usuario.estado_id = payload.estado
    await db.commit()
    return {"status": "ok", "estado": payload.estado}

# ================================
# CREAR ADMINISTRADOR
# ================================
@router.post("/", response_model=dict)
async def create_admin(payload: AdminCreate, db: AsyncSession = Depends(get_db)):
    # Validar correo único
    existing = await db.execute(select(Usuario).where(Usuario.correo == payload.correo))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    # Crear usuario
    nuevo = Usuario(
        tipo_documento_id=payload.tipo_documento_id or 1,
        documento=payload.documento or "N/A",
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        correo=payload.correo,
        telefono=payload.telefono,
        contrasena=payload.contrasena,
        estado_id=1
    )
    db.add(nuevo)
    await db.flush()  # genera id_usuario sin commit todavía

    # Crear rol administrador
    usuario_rol = UsuarioRol(
        user_id=nuevo.id_usuario,
        rol_id=2,
        restaurante_id=payload.restaurante_id
    )
    db.add(usuario_rol)

    await db.commit()
    await db.refresh(nuevo)

    return {"status": "ok", "admin_id": nuevo.id_usuario}

# ================================
# LISTAR RESTAURANTES
# ================================
@router.get("/restaurantes", response_model=List[RestauranteOut])
async def list_restaurantes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Restaurante))
    restaurantes = result.scalars().all()
    return restaurantes
