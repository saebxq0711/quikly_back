from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.repositories.pedido_repo import (
    get_pedidos_summary,
    get_top_restaurants_by_sales,
    get_top_products,
    get_pedidos,
)
from datetime import date
from fastapi.responses import StreamingResponse
from io import BytesIO

from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

router = APIRouter(
    prefix="/superadmin/pedidos",
    tags=["SuperAdmin Pedidos"]
)


# ==========================
# DATA
# ==========================
@router.get("/summary")
async def summary(
    from_date: date,
    to_date: date,
    restaurante_id: int | None = None,
    estado_id: int | None = None,
    db=Depends(get_db)
):
    return await get_pedidos_summary(db, from_date, to_date)


@router.get("/top-restaurantes")
async def top_restaurants(
    from_date: date,
    to_date: date,
    db=Depends(get_db)
):
    return await get_top_restaurants_by_sales(db, from_date, to_date)


@router.get("/top-productos")
async def top_products(
    from_date: date,
    to_date: date,
    db=Depends(get_db)
):
    return await get_top_products(db, from_date, to_date)


# ==========================
# EXPORT EXCEL
# ==========================
@router.get("/export/excel")
async def export_excel(
    from_date: date,
    to_date: date,
    restaurante_id: int | None = None,
    estado_id: int | None = None,
    db=Depends(get_db)
):
    summary = await get_pedidos_summary(db, from_date, to_date)

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen Pedidos"

    ws.append(["Métrica", "Valor"])
    ws.append(["Total pedidos", summary["total_pedidos"]])
    ws.append(["Total vendido", summary["total_vendido"]])
    ws.append(["Ticket promedio", summary["ticket_promedio"]])
    ws.append(["En preparación", summary["estados"]["en_preparacion"]])
    ws.append(["Pendiente", summary["estados"]["pendiente"]])
    ws.append(["Rechazado", summary["estados"]["rechazado"]])
    ws.append(["Entregado", summary["estados"]["entregado"]])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=reporte_pedidos.xlsx"
        }
    )


# ==========================
# EXPORT PDF
# ==========================
@router.get("/export/pdf")
async def export_pdf(
    from_date: date,
    to_date: date,
    restaurante_id: int | None = None,
    estado_id: int | None = None,
    db=Depends(get_db)
):
    summary = await get_pedidos_summary(db, from_date, to_date)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("Reporte de Pedidos", styles["Title"]),
        Paragraph(f"Total pedidos: {summary['total_pedidos']}", styles["Normal"]),
        Paragraph(f"Total vendido: ${summary['total_vendido']}", styles["Normal"]),
        Paragraph(f"Ticket promedio: ${summary['ticket_promedio']}", styles["Normal"]),
        Paragraph(f"En preparación: {summary['estados']['en_preparacion']}", styles["Normal"]),
        Paragraph(f"Pendiente: {summary['estados']['pendiente']}", styles["Normal"]),
        Paragraph(f"Rechazado: {summary['estados']['rechazado']}", styles["Normal"]),
        Paragraph(f"Entregado: {summary['estados']['entregado']}", styles["Normal"]),
    ]

    doc.build(content)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_pedidos.pdf"
        }
    )


# ==========================
# LISTADO DE PEDIDOS
# ==========================
@router.get("")
async def list_pedidos(
    from_date: date,
    to_date: date,
    restaurante_id: int | None = None,
    estado_id: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await get_pedidos(
        db=db,
        from_date=from_date,
        to_date=to_date,
        restaurante_id=restaurante_id,
        estado_id=estado_id,
        page=page,
        limit=limit,
    )
