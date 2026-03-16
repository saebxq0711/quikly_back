import httpx
import time
from datetime import date

from app.core.config import settings
from app.integrations.siigo.auth import get_siigo_token


async def create_invoice(customer, cart, total):

    token = await get_siigo_token()

    base_url = settings.siigo_base_url

    headers = {
        "Authorization": f"Bearer {token}",
        "Partner-Id": "SandboxSiigoAPI",
        "Content-Type": "application/json"
    }

    # =========================
    # Convertir carrito a items
    # =========================

    items = []

    for item in cart:

        items.append({
            "code": "VENTA_COMIDA",
            "description": item["nombre"],
            "quantity": item["cantidad"],
            "price": item["precio"],
            "discount": 0
        })

        # extras
        for op in item.get("seleccion", []):

            if op.get("precio_adicional", 0) > 0:

                items.append({
                    "code": "VENTA_EXTRAS",
                    "description": op["nombre_opcion"],
                    "quantity": item["cantidad"],
                    "price": op["precio_adicional"],
                    "discount": 0
                })

    # =========================
    # separar nombre
    # =========================

    names = customer["name"].split(" ")

    first = names[0]
    last = names[1] if len(names) > 1 else ""

    # =========================
    # numero base factura
    # =========================

    base_number = int(time.time())

    payload = {

        "document": {
            "id": 28231
        },

        "date": str(date.today()),

        "number": base_number,

        "customer": {
            "person_type": "Person",
            "id_type": "13",
            "identification": customer["documentNumber"],
            "branch_office": 0,

            "name": [
                first,
                last
            ],

            "address": {
                "address": "Consumidor final",
                "city": {
                    "country_code": "Co",
                    "country_name": "Colombia",
                    "state_code": "11",
                    "state_name": "Bogotá",
                    "city_code": "11001",
                    "city_name": "Bogotá"
                },
                "postal_code": "110111"
            },

            "phones": [
                {
                    "indicative": "57",
                    "number": customer["phone"].replace("+57", ""),
                    "extension": ""
                }
            ],

            "contacts": [
                {
                    "first_name": first,
                    "email": customer["email"],
                    "phone": {
                        "indicative": "57",
                        "number": customer["phone"].replace("+57", ""),
                        "extension": ""
                    }
                }
            ]
        },

        "seller": 901,

        "stamp": {
            "send": True
        },

        "mail": {
            "send": True
        },

        "observations": "Pedido kiosco Quikly",

        "items": items,

        "payments": [
            {
                "id": 8147,
                "value": total,
                "due_date": str(date.today())
            }
        ],

        "additional_fields": {}
    }

    create_url = f"{base_url}/v1/invoices"

    # =========================
    # crear factura con retry
    # =========================

    async with httpx.AsyncClient(timeout=30) as client:

        for i in range(5):

            payload["number"] = base_number + i

            response = await client.post(
                create_url,
                json=payload,
                headers=headers
            )

            if response.status_code < 400:

                created_invoice = response.json()

                invoice_id = created_invoice["id"]

                # =========================
                # consultar factura completa
                # =========================

                invoice_url = f"{base_url}/v1/invoices/{invoice_id}"

                invoice_response = await client.get(
                    invoice_url,
                    headers=headers
                )

                if invoice_response.status_code >= 400:
                    raise Exception(invoice_response.text)

                return invoice_response.json()

            error = response.text

            print("SIIGO ERROR:")
            print(error)

            if "number" not in error.lower():
                raise Exception(error)

    raise Exception("No se pudo generar un número de factura válido")