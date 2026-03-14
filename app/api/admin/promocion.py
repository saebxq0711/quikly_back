from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, time
import os, uuid

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.promocion import Promocion
from app.models.promocion_producto import PromocionProducto
from app.models.usuarios_rol import UsuarioRol
from app.models.producto import Producto

UPLOAD_DIR = "uploads/flyers"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(
    prefix="/admin/restaurante",
    tags=["Admin Restaurante - Promociones y Productos"]
)

# ---------------------
# Helper: obtener restaurante del admin
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
# Listar productos
# ---------------------
@router.get("/productos/")
async def listar_productos(admin=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    restaurante_id = await get_admin_restaurante_id(admin, db)
    stmt = select(Producto).where(Producto.restaurante_id == restaurante_id, Producto.estado_id == 1)
    productos = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": p.id_producto,
            "nombre": p.nombre,
            "precio": float(p.precio_base),
            "descripcion": p.descripcion,
            "img": p.img_producto
        } for p in productos
    ]

# ---------------------
# Crear promoción
# ---------------------
@router.post("/promocion/")
async def crear_promocion(
    titulo: str = Body(...),
    descripcion: str | None = Body(None),
    dias_semana: str = Body(...),
    hora_inicio: str = Body(...),
    hora_fin: str = Body(...),
    fecha_inicio: str | None = Body(None),
    fecha_fin: str | None = Body(None),
    estado_id: int = Body(1),
    flyer: UploadFile | None = File(None),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    filename = None
    if flyer:
        if flyer.content_type not in ["image/png", "image/jpeg", "image/webp"]:
            raise HTTPException(400, "Formato de imagen no permitido")
        filename = f"{uuid.uuid4().hex}_{flyer.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(await flyer.read())

    # Validar hora
    try:
        hora_inicio_obj = time.fromisoformat(hora_inicio)
        hora_fin_obj = time.fromisoformat(hora_fin)
    except ValueError:
        raise HTTPException(400, "Formato de hora inválido. Use HH:MM")

    fecha_inicio_obj = datetime.fromisoformat(fecha_inicio) if fecha_inicio else None
    fecha_fin_obj = datetime.fromisoformat(fecha_fin) if fecha_fin else None

    promo = Promocion(
        restaurante_id=restaurante_id,
        titulo=titulo.strip(),
        descripcion=descripcion.strip() if descripcion else None,
        img_flyer=f"/{UPLOAD_DIR}/{filename}" if filename else None,
        dias_semana=dias_semana.strip(),
        hora_inicio=hora_inicio_obj,
        hora_fin=hora_fin_obj,
        fecha_inicio=fecha_inicio_obj,
        fecha_fin=fecha_fin_obj,
        estado_id=estado_id
    )

    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return promo

# ---------------------
# Agregar productos a promoción
# ---------------------
@router.post("/promocion/{promocion_id}/producto")
async def agregar_producto_promocion(
    promocion_id: int,
    producto_id: int = Body(...),
    tipo_descuento: str = Body(...),   # "porcentaje" | "monto"
    valor_descuento: float = Body(...),
    db: AsyncSession = Depends(get_db)
):
    tipo_descuento_normalizado = tipo_descuento.strip().lower()

    if tipo_descuento_normalizado not in ["porcentaje", "monto"]:
        raise HTTPException(400, "Tipo de descuento inválido. Debe ser 'porcentaje' o 'monto'")

    if tipo_descuento_normalizado == "porcentaje" and not (0 <= valor_descuento <= 100):
        raise HTTPException(400, "El descuento por porcentaje debe estar entre 0 y 100")
    if tipo_descuento_normalizado == "monto" and valor_descuento < 0:
        raise HTTPException(400, "El descuento por monto no puede ser negativo")

    pp = PromocionProducto(
        promocion_id=promocion_id,
        producto_id=producto_id,
        tipo_descuento=tipo_descuento_normalizado,
        valor_descuento=valor_descuento
    )
    db.add(pp)
    await db.commit()
    await db.refresh(pp)
    return pp

# ---------------------
# Listar promociones
# ---------------------
@router.get("/promocion/")
async def listar_promociones(admin=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    restaurante_id = await get_admin_restaurante_id(admin, db)
    stmt = select(Promocion).where(Promocion.restaurante_id == restaurante_id)
    promociones = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id_promocion": p.id_promocion,
            "titulo": p.titulo,
            "descripcion": p.descripcion,
            "img_flyer": p.img_flyer,
            "dias_semana": p.dias_semana,
            "hora_inicio": p.hora_inicio.strftime("%H:%M"),
            "hora_fin": p.hora_fin.strftime("%H:%M"),
            "estado_id": p.estado_id
        } for p in promociones
    ]

# ---------------------
# PATCH: Cambiar estado de promoción
# ---------------------
@router.patch("/promocion/{promocion_id}/estado")
async def cambiar_estado_promocion(
    promocion_id: int,
    payload: dict = Body(...),  # recibir todo como dict
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_user)
):
    restaurante_id = await get_admin_restaurante_id(admin, db)
    stmt = select(Promocion).where(Promocion.id_promocion == promocion_id, Promocion.restaurante_id == restaurante_id)
    promo = (await db.execute(stmt)).scalar_one_or_none()
    if not promo:
        raise HTTPException(404, "Promoción no encontrada")

    estado_id = payload.get("estado_id")
    if estado_id not in [1, 2]:
        raise HTTPException(400, "Estado inválido")

    promo.estado_id = estado_id
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return {
        "id_promocion": promo.id_promocion,
        "titulo": promo.titulo,
        "estado_id": promo.estado_id
    }
