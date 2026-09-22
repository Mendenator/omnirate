import io

import piexif
from PIL import Image

from app.core.uploads import strip_exif


def _jpeg_with_gps_exif() -> bytes:
    img = Image.new("RGB", (4, 4), color="red")
    gps_ifd = {piexif.GPSIFD.GPSLatitudeRef: b"N", piexif.GPSIFD.GPSLatitude: ((47, 1), (55, 1), (0, 1))}
    exif_bytes = piexif.dump({"GPS": gps_ifd})
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif_bytes)
    return buf.getvalue()


def test_strip_exif_removes_gps_data():
    original = _jpeg_with_gps_exif()
    assert Image.open(io.BytesIO(original)).info.get("exif")  # sanity: GPS was actually embedded

    cleaned = strip_exif(original)
    cleaned_img = Image.open(io.BytesIO(cleaned))
    assert not cleaned_img.info.get("exif")


def test_strip_exif_preserves_pixel_data():
    original = _jpeg_with_gps_exif()
    cleaned = strip_exif(original)

    original_pixels = list(Image.open(io.BytesIO(original)).convert("RGB").getdata())
    cleaned_pixels = list(Image.open(io.BytesIO(cleaned)).convert("RGB").getdata())
    assert original_pixels == cleaned_pixels
