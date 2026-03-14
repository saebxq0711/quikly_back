import jwt
from datetime import datetime
from app.services.webhook_log_service import save_webhook_log
from app.core.config import settings


async def process_qr_notification(body: dict, authorization: str | None):

    token = None

    # token en body
    if body.get("token"):
        token = body["token"]

    # token en header
    elif authorization:
        token = authorization.replace("Bearer ", "")

    if not token:
        await save_webhook_log({
            "status": "token_missing",
            "raw_body": body,
            "received_at": str(datetime.utcnow())
        })
        raise Exception("Token not provided")

    try:

        decoded = jwt.decode(
            token,
            settings.bancolombia_public_key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )

    except jwt.ExpiredSignatureError:

        await save_webhook_log({
            "status": "token_expired",
            "raw_body": body,
            "received_at": str(datetime.utcnow())
        })

        raise

    except jwt.InvalidTokenError as e:

        await save_webhook_log({
            "status": "invalid_signature",
            "error": str(e),
            "raw_body": body,
            "received_at": str(datetime.utcnow())
        })

        raise

    transaction = {
        "qr_id": decoded.get("qrId"),
        "amount": decoded.get("amount"),
        "status": decoded.get("status"),
        "reference": decoded.get("transactionReference"),
        "date": decoded.get("transactionDate")
    }

    await save_webhook_log({
        "status": "success",
        "transaction": transaction,
        "raw_body": body,
        "received_at": str(datetime.utcnow())
    })

    print("PAGO RECIBIDO:", transaction)

    # aquí puedes actualizar tu pedido en DB