from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promocion_producto import PromocionProducto
from app.models.promocion import Promocion


def promocion_activa(promocion: Promocion):
    ahora = datetime.now()

    if promocion.estado_id != 1:
        return False

    if promocion.fecha_inicio and ahora.date() < promocion.fecha_inicio:
        return False

    if promocion.fecha_fin and ahora.date() > promocion.fecha_fin:
        return False

    if promocion.hora_inicio and ahora.time() < promocion.hora_inicio:
        return False

    if promocion.hora_fin and ahora.time() > promocion.hora_fin:
        return False

    if promocion.dias_semana:
        dias = [int(d) for d in promocion.dias_semana.split(",")]
        if ahora.weekday() not in dias:
            return False

    return True


async def calcular_precio_con_promocion(
    db: AsyncSession,
    producto_id: int,
    precio_base: float,
):
    stmt = (
        select(PromocionProducto)
        .join(Promocion)
        .options(selectinload(PromocionProducto.promocion))
        .where(
            PromocionProducto.producto_id == producto_id,
            Promocion.estado_id == 1,
        )
    )

    result = await db.execute(stmt)
    promos = result.scalars().all()

    precio_final = precio_base
    promo_activa = None

    for promo in promos:

        if not promo.promocion:
            continue

        if not promocion_activa(promo.promocion):
            continue

        tipo = promo.tipo_descuento.lower()

        if tipo == "porcentaje":
            precio_final = precio_base * (1 - float(promo.valor_descuento) / 100)

        elif tipo == "monto":
            precio_final = max(0, precio_base - float(promo.valor_descuento))

        precio_final = round(precio_final, 2)

        promo_activa = {
            "id_promocion": promo.promocion_id,
            "tipo_descuento": promo.tipo_descuento,
            "valor_descuento": float(promo.valor_descuento),
        }

        break

    return precio_final, promo_activa