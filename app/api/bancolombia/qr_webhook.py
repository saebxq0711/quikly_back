from fastapi import APIRouter, Request, Header
import asyncio
from app.integrations.bancolombia.webhook import process_qr_notification

router = APIRouter()


@router.post("/bancolombia/qr-notification")
async def bancolombia_qr_notification(
    request: Request,
    authorization: str | None = Header(None)
):
    body = await request.json()

    asyncio.create_task(
        process_qr_notification(body, authorization)
    )

    return {"status": "received"}