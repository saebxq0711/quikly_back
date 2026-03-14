from fastapi import APIRouter

from app.integrations.siigo.invoice_service import create_invoice

router = APIRouter(
    prefix="/kiosco/factura",
    tags=["Kiosco Factura"]
)


@router.post("/crear")
async def crear_factura(payload: dict):

    invoice = await create_invoice(
        payload["customer"],
        payload["cart"],
        payload["total"]
    )

    return invoice