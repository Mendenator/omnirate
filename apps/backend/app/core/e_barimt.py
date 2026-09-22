"""e-barimt (Mongolia e-invoice) QR verification client.

⛔ EXTERNAL DEPENDENCY (see docs/PROGRESS.md): production use requires e-barimt
API access from the tax authority. `settings.e_barimt_use_mock` routes at a
local mock so the PoE pipeline (P1-05) can be built and tested end-to-end
before that access lands. Risk mitigation per SOW §7: if e-barimt access is
denied, OCR (P1-03) + GPS (P2-01) evidence substitutes and the PoE weight for
that path stays at 0.70 (see app/domain/poe.py comment for the swap point).
"""

from dataclasses import dataclass
from datetime import datetime

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class EBarimtReceiptData:
    ddtd: str  # receipt number
    ttd: str  # merchant taxpayer registration number
    amount: float
    purchased_at: datetime


async def verify_qr_payload(qr_payload: str) -> EBarimtReceiptData:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(settings.e_barimt_verify_url, params={"qr": qr_payload})
        resp.raise_for_status()
        body = resp.json()

    return EBarimtReceiptData(
        ddtd=body["ddtd"],
        ttd=body["ttd"],
        amount=float(body["amount"]),
        purchased_at=datetime.fromisoformat(body["purchased_at"]),
    )
