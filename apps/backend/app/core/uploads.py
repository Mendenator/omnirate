"""Presigned upload + server-side EXIF stripping (P1-02).

Flow: client asks for a presigned PUT URL, uploads directly to S3 (bypassing
our API for the bytes), then the `strip_exif` worker job (triggered by an S3
event notification in prod, or called directly after upload in dev) rewrites
the object with EXIF metadata removed — GPS tags specifically, since a photo's
embedded location can deanonymize a reviewer.

Acceptance: 0 files with EXIF GPS surviving in the bucket.
"""

import io
import uuid
from typing import Any

import boto3
from PIL import Image

from app.core.config import get_settings


def get_s3_client() -> Any:
    # boto3 ships no inline type stubs (would need the separate boto3-stubs /
    # mypy-boto3-s3 packages); Any here is the honest type without adding
    # that dependency just to satisfy mypy.
    return boto3.client("s3")


def presign_upload(*, content_type: str) -> tuple[str, str]:
    """Returns (upload_id, presigned_put_url). Object key is server-generated
    (never client-supplied) to prevent path traversal / overwrite of another
    user's object."""
    settings = get_settings()
    upload_id = str(uuid.uuid4())
    key = f"pending/{upload_id}"
    url = get_s3_client().generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.uploads_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=600,
    )
    return upload_id, url


def strip_exif(image_bytes: bytes) -> bytes:
    """Returns a copy of the image with all EXIF (including GPS) removed.
    Re-encoding without exif=... (rather than deleting individual tags) is
    the only approach that's robust to Pillow/library-specific tag quirks.
    """
    img = Image.open(io.BytesIO(image_bytes))
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))
    out = io.BytesIO()
    clean.save(out, format=img.format)
    return out.getvalue()


def finalize_upload(*, upload_id: str) -> str:
    """Moves pending/{upload_id} -> uploads/{upload_id} after stripping EXIF.
    Returns the final object key."""
    settings = get_settings()
    client = get_s3_client()
    pending_key = f"pending/{upload_id}"
    final_key = f"uploads/{upload_id}"

    obj = client.get_object(Bucket=settings.uploads_bucket, Key=pending_key)
    body = obj["Body"].read()

    if len(body) > settings.uploads_max_bytes:
        client.delete_object(Bucket=settings.uploads_bucket, Key=pending_key)
        raise ValueError(f"upload exceeds {settings.uploads_max_bytes} bytes")

    cleaned = strip_exif(body)
    client.put_object(Bucket=settings.uploads_bucket, Key=final_key, Body=cleaned, ContentType=obj["ContentType"])
    client.delete_object(Bucket=settings.uploads_bucket, Key=pending_key)
    return final_key
