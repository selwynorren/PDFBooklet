# PDFBooklet/tests/test_downscaler.py
"""
Verifies image downscaling-on-save behaves as designed:
  - OFF by default (no downscaling unless requested),
  - progressive (lower target DPI -> smaller images),
  - NEVER upscales (a low-res image is left untouched even at high target DPI).

Only DCTDecode (JPEG) images are downsampled (FlateDecode is intentionally
skipped in image_downscaler), so these fixtures embed JPEGs.
"""

import io
import fitz
from PIL import Image
from pypdf import PdfReader

from src.logic.pdf_saver import PDFSaver


def _pdf_with_jpeg(tmp_path, px):
    img = Image.new("RGB", (px, px), (120, 60, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    doc = fitz.open()
    page = doc.new_page(width=300, height=300)
    page.insert_image(fitz.Rect(0, 0, 300, 300), stream=buf.getvalue())
    path = str(tmp_path / f"img_{px}.pdf")
    doc.save(path)
    doc.close()
    return path


def _walk(resources, dims):
    xobj = resources.get("/XObject") if resources else None
    if not xobj:
        return
    xobj = xobj.get_object()
    for name in xobj:
        obj = xobj[name].get_object()
        if obj.get("/Subtype") == "/Image":
            dims.append(max(int(obj["/Width"]), int(obj["/Height"])))
        elif obj.get("/Subtype") == "/Form" and "/Resources" in obj:
            _walk(obj["/Resources"].get_object(), dims)


def _max_image_dim(path):
    dims = []
    for page in PdfReader(path).pages:
        if "/Resources" in page:
            _walk(page["/Resources"].get_object(), dims)
    return max(dims) if dims else None


def test_no_downscale_by_default(tmp_path):
    src = _pdf_with_jpeg(tmp_path, 4000)
    out = str(tmp_path / "out.pdf")
    PDFSaver.save_booklet(src, out, [0], "single", 300, 300, downscale_images=False)
    assert _max_image_dim(out) == 4000  # untouched


def test_downscale_reduces_high_res(tmp_path):
    src = _pdf_with_jpeg(tmp_path, 4000)
    out = str(tmp_path / "out.pdf")
    PDFSaver.save_booklet(
        src, out, [0], "single", 300, 300, downscale_images=True, target_dpi=72
    )
    # target_pixels = 11in * 72dpi = 792
    assert _max_image_dim(out) <= 792


def test_downscale_never_upscales(tmp_path):
    src = _pdf_with_jpeg(tmp_path, 200)
    out = str(tmp_path / "out.pdf")
    PDFSaver.save_booklet(
        src, out, [0], "single", 300, 300, downscale_images=True, target_dpi=1200
    )
    assert _max_image_dim(out) == 200  # low-res left alone, not upscaled


def test_downscale_is_progressive(tmp_path):
    src = _pdf_with_jpeg(tmp_path, 4000)
    out72 = str(tmp_path / "out72.pdf")
    out300 = str(tmp_path / "out300.pdf")
    PDFSaver.save_booklet(src, out72, [0], "single", 300, 300, downscale_images=True, target_dpi=72)
    PDFSaver.save_booklet(src, out300, [0], "single", 300, 300, downscale_images=True, target_dpi=300)
    assert _max_image_dim(out72) < _max_image_dim(out300)  # lower DPI -> smaller
