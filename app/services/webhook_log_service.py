import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("logs/bancolombia_qr_webhooks.log")

LOG_FILE.parent.mkdir(exist_ok=True)


async def save_webhook_log(data: dict):

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")