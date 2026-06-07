# PDFBooklet/tests/test_save_centering.py
"""
Regression test for a centering bug in the save path.

When a source page fits a target at exactly scale 1.0 in one dimension but is
smaller in the other, it must still be CENTERED in the target rect. A former
special-case (`if base_scale == 1.0: translate to origin`) skipped centering and
parked the page in the bottom-left corner.

Verifies the content-stream CTM places content at the centered offset.
"""

import re
import fitz
import pytest
from pypdf import PdfReader

from src.logic.pdf_saver import PDFSaver

_CTM_RE = re.compile(
    r"([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) cm"
)


def _content_pdf(tmp_path, w, h):
    doc = fitz.open()
    page = doc.new_page(width=w, height=h)
    page.insert_text((10, 30), "X")            # ensure the page has a content stream
    page.draw_rect(fitz.Rect(2, 2, w - 2, h - 2))
    path = str(tmp_path / f"src_{w}x{h}.pdf")
    doc.save(path)
    doc.close()
    return path


def _ctm(out_path):
    page = PdfReader(out_path).pages[0]
    data = page.get_contents().get_data().decode("latin-1")
    m = _CTM_RE.search(data)
    assert m, "no CTM found in content stream"
    a, b, c, d, e, f = (float(g) for g in m.groups())
    return a, d, e, f  # scale_x, scale_y, tx, ty


def test_scale1_centered_vertically(tmp_path):
    """src 100x200 on 100x300 target: scale 1.0, must center vertically (ty=50)."""
    src = _content_pdf(tmp_path, 100, 200)
    out = str(tmp_path / "out.pdf")
    ok, err = PDFSaver.save_booklet(src, out, [0], "single", 100, 300)
    assert ok, err
    sx, sy, tx, ty = _ctm(out)
    assert sx == pytest.approx(1.0, abs=1e-6)
    assert tx == pytest.approx(0.0, abs=0.5)
    assert ty == pytest.approx(50.0, abs=0.5)   # (300-200)/2


def test_scale1_centered_horizontally(tmp_path):
    """src 100x200 on 300x200 target: scale 1.0, must center horizontally (tx=100)."""
    src = _content_pdf(tmp_path, 100, 200)
    out = str(tmp_path / "out.pdf")
    ok, err = PDFSaver.save_booklet(src, out, [0], "single", 300, 200)
    assert ok, err
    sx, sy, tx, ty = _ctm(out)
    assert sx == pytest.approx(1.0, abs=1e-6)
    assert tx == pytest.approx(100.0, abs=0.5)  # (300-100)/2
    assert ty == pytest.approx(0.0, abs=0.5)
