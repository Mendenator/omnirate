"""Receipt image duplicate + forgery detection (P1-04).

pHash catches "same photo submitted twice" (including re-compressed/resized
copies — the whole point of a perceptual hash over a cryptographic one). ELA
(Error Level Analysis) flags localized edits: resaving a JPEG at a known
quality and diffing against the original makes edited regions (where a
digit was pasted over) stand out because they compress differently than the
rest of the (already-once-compressed) image.

Acceptance: duplicate recall >=95%, FP <=2% — those targets need tuning
against real submitted photos (P1 pilot data), so DUPLICATE_HAMMING_THRESHOLD
and ELA_SUSPICIOUS_THRESHOLD below are starting points, not final values.
"""

import io
from dataclasses import dataclass

import imagehash
from PIL import Image, ImageChops

DUPLICATE_HAMMING_THRESHOLD = 8  # pHash bit-distance below which two images count as "the same receipt"
ELA_SUSPICIOUS_THRESHOLD = 40  # mean ELA pixel diff above which we flag possible tampering
ELA_JPEG_QUALITY = 90


@dataclass(frozen=True)
class ForensicsResult:
    phash: str
    is_likely_duplicate_of: list[str]
    ela_mean_diff: float
    is_likely_tampered: bool


def compute_phash(image_bytes: bytes) -> imagehash.ImageHash:
    return imagehash.phash(Image.open(io.BytesIO(image_bytes)))


def find_duplicates(phash: imagehash.ImageHash, known_hashes: dict[str, imagehash.ImageHash]) -> list[str]:
    return [
        receipt_id
        for receipt_id, other in known_hashes.items()
        if (phash - other) <= DUPLICATE_HAMMING_THRESHOLD
    ]


def compute_ela_mean_diff(image_bytes: bytes) -> float:
    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    resaved_buf = io.BytesIO()
    original.save(resaved_buf, format="JPEG", quality=ELA_JPEG_QUALITY)
    resaved = Image.open(io.BytesIO(resaved_buf.getvalue())).convert("RGB")

    diff = ImageChops.difference(original, resaved)
    pixels = list(diff.getdata())
    total = sum(sum(px) for px in pixels)
    return total / (len(pixels) * 3) if pixels else 0.0


def analyze_receipt_image(image_bytes: bytes, known_hashes: dict[str, imagehash.ImageHash]) -> ForensicsResult:
    phash = compute_phash(image_bytes)
    duplicates = find_duplicates(phash, known_hashes)
    ela_diff = compute_ela_mean_diff(image_bytes)

    return ForensicsResult(
        phash=str(phash),
        is_likely_duplicate_of=duplicates,
        ela_mean_diff=ela_diff,
        is_likely_tampered=ela_diff > ELA_SUSPICIOUS_THRESHOLD,
    )
