from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.core.security import get_kiosco_context
from app.schemas.auth import KioscoContext

from app.models.producto import Producto
from app.models.grupo_opcion_producto import GrupoOpcionProducto

from app.services.promociones import calcular_precio_con_promocion


router = APIRouter(
    prefix="/kiosco",
    tags=["Kiosco"],
)


# =========================================================
# Helper para formatear promoción
# =========================================================
def formatear_promocion(promocion, precio_base: float):

    if not promocion:
        return False, None

    tipo = promocion["tipo_descuento"].lower()
    valor = float(promocion["valor_descuento"])

    porcentaje_descuento = None

    if tipo == "porcentaje":
        porcentaje_descuento = round(valor)

    elif tipo == "monto":
        if precio_base > 0:
            porcentaje_descuento = round((valor / precio_base) * 100)

    return True, porcentaje_descuento


# =========================================================
# Productos por categoría
# =========================================================
@router.get("/categorias/{categoria_id}/productos")
async def get_productos_por_categoria(
    categoria_id: int,
    ctx: KioscoContext = Depends(get_kiosco_context),
    db: AsyncSession = Depends(get_db),
):

    stmt = (
        select(Producto)
        .options(
            selectinload(Producto.grupos_opcion)
            .selectinload(GrupoOpcionProducto.opciones)
        )
        .where(
            Producto.restaurante_id == ctx.restaurante_id,
            Producto.categoria_id == categoria_id,
            Producto.estado_id == 1,
        )
        .order_by(Producto.nombre.asc())
    )

    result = await db.execute(stmt)
    productos = result.scalars().unique().all()

    response = []

    for p in productos:

        precio_base = float(p.precio_base)

        precio_final, promocion = await calcular_precio_con_promocion(
            db,
            p.id_producto,
            precio_base,
        )

        tiene_promocion, porcentaje_descuento = formatear_promocion(
            promocion,
            precio_base,
        )

        grupos = []

        for g in p.grupos_opcion:
            if g.estado_id != 1:
                continue

            opciones = [
                {
                    "id": o.id_opcion_producto,
                    "nombre": o.nombre,
                    "precio_adicional": float(o.precio_adicional),
                }
                for o in g.opciones
                if o.estado_id == 1
            ]

            if g.obligatorio and not opciones:
                continue

            grupos.append({
                "id": g.id_grupo_opcion,
                "nombre": g.nombre,
                "tipo": g.tipo,
                "obligatorio": g.obligatorio,
                "min": g.min_selecciones,
                "max": g.max_selecciones,
                "opciones": opciones,
            })

        response.append({
            "id": p.id_producto,
            "nombre": p.nombre,
            "descripcion": p.descripcion,

            "precio_base": precio_base,
            "precio_final": precio_final,

            "tiene_promocion": tiene_promocion,
            "porcentaje_descuento": porcentaje_descuento,

            "img": p.img_producto,
            "grupos_opcion": grupos,
        })

    return response


# =========================================================
# Productos sugeridos
# =========================================================
@router.get("/productos/sugeridos")
async def get_productos_sugeridos(
    limit: int = 4,
    exclude_ids: str | None = None,
    ctx: KioscoContext | None = Depends(get_kiosco_context),
    db: AsyncSession = Depends(get_db),
):
    if not ctx:
        return []

    exclude_list: list[int] = []
    if exclude_ids:
        exclude_list = [
            int(x) for x in exclude_ids.split(",") if x.isdigit()
        ]

    stmt = select(Producto).where(
        Producto.restaurante_id == ctx.restaurante_id,
        Producto.estado_id == 1,
    )

    if exclude_list:
        stmt = stmt.where(~Producto.id_producto.in_(exclude_list))

    stmt = stmt.order_by(func.random()).limit(limit)

    result = await db.execute(stmt)
    productos = result.scalars().all()

    # 🔥 FILTRO FINAL DEFENSIVO (por si SQLAlchemy o DB hacen cosas raras)
    productos = [p for p in productos if p.estado_id == 1]

    response = []

    for p in productos:
        print("DEBUG FINAL:", p.id_producto, p.estado_id)

        precio_base = float(p.precio_base)

        precio_final, promocion = await calcular_precio_con_promocion(
            db,
            p.id_producto,
            precio_base,
        )

        tiene_promocion, porcentaje_descuento = formatear_promocion(
            promocion,
            precio_base,
        )

        response.append({
            "id": p.id_producto,
            "nombre": p.nombre,
            "precio_base": precio_base,
            "precio_final": precio_final,
            "tiene_promocion": tiene_promocion,
            "porcentaje_descuento": porcentaje_descuento,
            "img": p.img_producto,
        })

    return response


# =========================================================
# Detalle de producto
# =========================================================
@router.get("/productos/{producto_id}")
async def get_producto_detalle(
    producto_id: int,
    ctx: KioscoContext = Depends(get_kiosco_context),
    db: AsyncSession = Depends(get_db),
):

    stmt = (
        select(Producto)
        .options(
            selectinload(Producto.grupos_opcion)
            .selectinload(GrupoOpcionProducto.opciones)
        )
        .where(
            Producto.id_producto == producto_id,
            Producto.restaurante_id == ctx.restaurante_id,
            Producto.estado_id == 1,
        )
    )

    result = await db.execute(stmt)
    producto = result.scalar_one_or_none()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    precio_base = float(producto.precio_base)

    precio_final, promocion = await calcular_precio_con_promocion(
        db,
        producto.id_producto,
        precio_base,
    )

    tiene_promocion, porcentaje_descuento = formatear_promocion(
        promocion,
        precio_base,
    )

    grupos = []

    for g in producto.grupos_opcion:
        if g.estado_id != 1:
            continue

        opciones = [
            {
                "id": o.id_opcion_producto,
                "nombre": o.nombre,
                "precio_adicional": float(o.precio_adicional),
            }
            for o in g.opciones
            if o.estado_id == 1
        ]

        if g.obligatorio and not opciones:
            continue

        grupos.append({
            "id": g.id_grupo_opcion,
            "nombre": g.nombre,
            "tipo": g.tipo,
            "obligatorio": g.obligatorio,
            "min": g.min_selecciones,
            "max": g.max_selecciones,
            "opciones": opciones,
        })

    return {
        "id": producto.id_producto,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,

        "precio_base": precio_base,
        "precio_final": precio_final,

        "tiene_promocion": tiene_promocion,
        "porcentaje_descuento": porcentaje_descuento,

        "img": producto.img_producto,
        "grupos_opcion": grupos,
    }