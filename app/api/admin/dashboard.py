from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.security import get_current_user
from app.repositories.admin.dashboard_repo import (
    get_dashboard_kpis,
    get_restaurante_info,
    get_admin_restaurante_id,
    get_pedidos_recientes,
    get_pedidos_por_hora,
    get_ventas_por_hora,
)

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin Restaurante - Dashboard"]
)



@router.get("/")
async def dashboard(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    restaurante_id = await get_admin_restaurante_id(db, current_user.id_usuario)
    if not restaurante_id:
        raise HTTPException(status_code=403, detail="Usuario no asociado a un restaurante")

    restaurante = await get_restaurante_info(db, restaurante_id)
    if not restaurante:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")

    kpis = await get_dashboard_kpis(db, restaurante_id)
    pedidos_recientes = await get_pedidos_recientes(db, restaurante_id)

    pedidos_recientes = [
        {
            "id_pedido": p.id_pedido,
            "total": float(p.total),
            "estado": {4:"Aprobado",5:"Pendiente",6:"Rechazado",7:"Entregado"}.get(p.estado_id,"Desconocido"),
            "hora": p.fecha_creacion.strftime("%H:%M"),
        }
        for p in pedidos_recientes
    ]

    pedidos_por_hora = await get_pedidos_por_hora(db, restaurante_id)
    ventas_por_hora = await get_ventas_por_hora(db, restaurante_id)

    return {
        "restaurante": {
            "id": restaurante["id_restaurante"],
            "nombre": restaurante["nombre"],
            "logo": restaurante["logo"],
        },
        "kpis": kpis,
        "pedidos_recientes": pedidos_recientes,
        "pedidos_por_hora": pedidos_por_hora,
        "ventas_por_hora": ventas_por_hora,
    }