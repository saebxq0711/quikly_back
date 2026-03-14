from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categoria import Categoria
from app.models.producto import Producto


async def get_restaurant_menu(db: AsyncSession, restaurante_id: int):
    categorias_stmt = (
        select(Categoria)
        .where(
            Categoria.restaurante_id == restaurante_id,
            Categoria.estado_id == 1
        )
        .order_by(Categoria.orden)
    )

    categorias = (await db.execute(categorias_stmt)).scalars().all()

    resultado = []

    for cat in categorias:
        productos_stmt = (
            select(Producto)
            .where(
                Producto.restaurante_id == restaurante_id,
                Producto.categoria_id == cat.id_categoria,
                Producto.estado_id == 1
            )
            .order_by(Producto.nombre)
        )

        productos = (await db.execute(productos_stmt)).scalars().all()

        resultado.append({
            "id_categoria": cat.id_categoria,
            "nombre": cat.nombre,
            "img_categoria": cat.img_categoria,
            "orden": cat.orden,
            "estado_id": cat.estado_id,
            "productos": [
                {
                    "id_producto": p.id_producto,
                    "nombre": p.nombre,
                    "descripcion": p.descripcion,
                    "precio_base": float(p.precio_base),
                    "img_producto": p.img_producto,
                    "estado_id": p.estado_id,
                }
                for p in productos
            ],
        })

    return resultado
