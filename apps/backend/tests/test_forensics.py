import io

from PIL import Image

from app.ml.forensics import compute_ela_mean_diff, compute_phash, find_duplicates


def _solid_jpeg(color) -> bytes:
    img = Image.new("RGB", (32, 32), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _gradient_jpeg(*, reversed_: bool) -> bytes:
    """pHash is a low-frequency structural hash — it deliberately ignores
    flat color (two solid-color images are indistinguishable to it, there's
    no frequency content at all) and is also fairly tolerant of *fine*
    texture differences like thin stripes (that detail lives in the high
    frequencies pHash's low-pass step discards). A dissimilarity test needs
    a difference in coarse, low-frequency structure — an inverted diagonal
    gradient is about as far apart as two 32x32 images get in that respect.
    """
    img = Image.new("RGB", (32, 32))
    for y in range(32):
        for x in range(32):
            v = int(255 * (x + y) / 62)
            if reversed_:
                v = 255 - v
            img.putpixel((x, y), (v, v, v))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_identical_images_have_zero_phash_distance():
    a = compute_phash(_solid_jpeg((200, 50, 50)))
    b = compute_phash(_solid_jpeg((200, 50, 50)))
    assert (a - b) == 0


def test_find_duplicates_matches_within_threshold():
    target = compute_phash(_solid_jpeg((10, 10, 10)))
    known = {"receipt-1": compute_phash(_solid_jpeg((10, 10, 10)))}
    assert find_duplicates(target, known) == ["receipt-1"]


def test_find_duplicates_excludes_dissimilar_images():
    target = compute_phash(_gradient_jpeg(reversed_=False))
    known = {"receipt-1": compute_phash(_gradient_jpeg(reversed_=True))}
    assert find_duplicates(target, known) == []


def test_ela_diff_is_low_for_freshly_saved_image():
    # A JPEG saved once at high quality, then re-saved at the ELA quality,
    # should show a small (not necessarily zero) mean diff.
    diff = compute_ela_mean_diff(_solid_jpeg((100, 100, 100)))
    assert diff < 5.0  # solid color compresses near-losslessly either way
