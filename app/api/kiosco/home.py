from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.auth import KioscoContext
from app.models.restaurante import Restaurante
from app.core.security import get_kiosco_context
from app.models.promocion import Promocion
from sqlalchemy import select, or_, and_
from datetime import datetime

router = APIRouter(
    prefix="/kiosco",
    tags=["Kiosco"]
)


    
@router.get("/context")
async def get_kiosco_home(
    ctx: KioscoContext = Depends(get_kiosco_context),
    db: AsyncSession = Depends(get_db),
):
    restaurante = await db.get(Restaurante, ctx.restaurante_id)

    if not restaurante:
        raise HTTPException(404, "Restaurante no encontrado")

    return {
        "restaurante": {
            "id": restaurante.id_restaurante,
            "nombre": restaurante.nombre,
            "logo": restaurante.logo,
        }
    }

@router.get("/promociones/activas")
async def get_promociones_activas(
    ctx: KioscoContext = Depends(get_kiosco_context),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now()
    current_day = now.isoweekday()  # 1-7
    current_time = now.time()
    today = datetime.now().date()

    stmt = (
    select(Promocion)
    .where(
        Promocion.restaurante_id == ctx.restaurante_id,
        Promocion.estado_id == 1,
        Promocion.img_flyer.isnot(None),
        Promocion.img_flyer != "",

        # Fecha (DATE vs DATE ✅)
        or_(
            Promocion.fecha_inicio == None,
            Promocion.fecha_inicio <= today,
        ),
        or_(
            Promocion.fecha_fin == None,
            Promocion.fecha_fin >= today,
        ),

        # Hora (TIME vs TIME ✅)
        or_(
            Promocion.hora_inicio == None,
            Promocion.hora_fin == None,
            and_(
                Promocion.hora_inicio <= current_time,
                Promocion.hora_fin >= current_time,
            ),
        ),
    )
)

    result = await db.execute(stmt)
    promociones = result.scalars().all()

    # Filtrar días (string "1,2,3")
    promociones_validas = []
    for promo in promociones:
        if not promo.dias_semana:
            promociones_validas.append(promo)
            continue

        dias = [int(d) for d in promo.dias_semana.split(",")]
        if current_day in dias:
            promociones_validas.append(promo)

    return [
        {
            "id": p.id_promocion,
            "titulo": p.titulo,
            "descripcion": p.descripcion,
            "img_flyer": p.img_flyer,
        }
        for p in promociones_validas
    ]