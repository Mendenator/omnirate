"""Printable PDF for a hospital-visit QR (P2-03). Pillow's own PDF writer is
used instead of pulling in a full PDF library (reportlab/weasyprint) — a
single QR image plus a caption doesn't need a layout engine.
"""

import io

import qrcode
from PIL import Image, ImageDraw, ImageFont


def render_qr_pdf(token: str, *, entity_name: str, expires_at_label: str) -> bytes:
    qr_img = qrcode.make(token).convert("RGB")

    canvas = Image.new("RGB", (qr_img.width, qr_img.height + 80), color="white")
    canvas.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((10, qr_img.height + 10), entity_name, fill="black", font=font)
    draw.text((10, qr_img.height + 40), f"Хүчинтэй хугацаа: {expires_at_label}", fill="black", font=font)

    out = io.BytesIO()
    canvas.save(out, format="PDF")
    return out.getvalue()
