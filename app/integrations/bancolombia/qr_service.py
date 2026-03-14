import httpx
import uuid
from app.core.config import settings
from app.integrations.bancolombia.auth import get_bancolombia_token


async def generate_qr(customer: dict, amount: int):

    token = await get_bancolombia_token()
    message_id = str(uuid.uuid4())

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-IBM-Client-Id": settings.bancolombia_client_id,
        "X-IBM-Client-Secret": settings.bancolombia_client_secret,
        "message-id": message_id
    }

    payload = {
        "data": {
            "nature": "DINAMICO",
            "purposeOfTransaction": "COMPRA",
            "customers": {
                "documentType": "NIT",
                "documentNumber": "890999876",
                "name": "Empresa S.A"
            },
            "commerce": {
                "merchantId": "3026540087",
                "salesPoint": {
                    "name": "CEOH Piso 4 Puesto 1587"
                },
                "checkout": {
                    "name": "Caja 4"
                },
                "seller": {
                    "name": "Gabriela"
                }
            },
            "transactions": {
                "businessReference": "Pago de mercado",
                "amount": 54800,
                "transactionReference": "Apartamento-901"
            },
            "aditionalNotificacion": [
                {
                    "contactPhone": "3014893355",
                    "email": "sede1@empresa.com"
                },
                {
                    "contactPhone": "3114893360",
                    "email": "sede2@empresa.com"
                }
            ]
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            settings.bancolombia_qr_url,
            json=payload,
            headers=headers
        )

    if response.status_code >= 400:
        print("Bancolombia QR ERROR:", response.text)
        raise Exception(response.text)

    data = response.json()

    qr_id = data["data"]["qrId"]
    qr_image = data["data"]["qrImage"]

    # Debug útil
    print("QR RAW:", qr_image[:80])

    # limpiar posibles saltos de línea
    qr_image = qr_image.replace("\n", "").replace("\r", "").strip()

    # Bancolombia devuelve SVG en base64
    qr_image = f"data:image/svg+xml;base64,{qr_image}"

    return {
        "qr_id": qr_id,
        "qr_image": qr_image
    }