from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

LOG_FILE = Path("logs/bancolombia_qr_webhooks.log")

@router.get("/superadmin/bancolombia/webhook-logs")
def download_logs():

    if not LOG_FILE.exists():
        return {"error": "No logs yet"}

    return FileResponse(
        LOG_FILE,
        filename="bancolombia_webhook_logs.log",
        media_type="text/plain"
    )