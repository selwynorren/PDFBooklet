# PDFBooklet/tests/test_processor_e2e.py
"""
End-to-end integration through BookletProcessor: load a real PDF, choose an
output size, generate the layout, and save. Exercises the full coordinator +
save chain (including the single-page -> sheet doubling) with real file I/O.
"""

import pytest
from pypdf import PdfReader

from src.logic.booklet_processor import BookletProcessor

MM_TO_PT = 72 / 25.4
A4_W, A4_H = 210 * MM_TO_PT, 297 * MM_TO_PT


def _save(proc, tmp_path, name):
    out = str(tmp_path / name)
    ok, err = proc.save_booklet(out, unit="mm")
    assert ok, err
    return out


def test_e2e_booklet(sample_pdf, tmp_path):
    proc = BookletProcessor(sample_pdf)
    proc.generate_booklet_layout(None, None)
    proc.set_output_size("a4")
    out = _save(proc, tmp_path, "booklet.pdf")
    pages = PdfReader(out).pages
    assert len(pages) == proc.get_page_count()
    # booklet sheet = 2x wide
    assert float(pages[0].mediabox.width) == pytest.approx(2 * A4_W, abs=1)
    assert float(pages[0].mediabox.height) == pytest.approx(A4_H, abs=1)
    proc.close()


def test_e2e_calendar(sample_pdf, tmp_path):
    proc = BookletProcessor(sample_pdf)
    proc.generate_calendar_layout(None, None)
    proc.set_output_size("a4")
    out = _save(proc, tmp_path, "calendar.pdf")
    pages = PdfReader(out).pages
    assert float(pages[0].mediabox.width) == pytest.approx(A4_W, abs=1)
    assert float(pages[0].mediabox.height) == pytest.approx(2 * A4_H, abs=1)
    proc.close()


def test_e2e_single(sample_pdf, tmp_path):
    proc = BookletProcessor(sample_pdf)
    proc.generate_single_page_layout(None, None)
    proc.set_output_size("a4")
    out = _save(proc, tmp_path, "single.pdf")
    pages = PdfReader(out).pages
    assert len(pages) == 6
    assert float(pages[0].mediabox.width) == pytest.approx(A4_W, abs=1)
    assert float(pages[0].mediabox.height) == pytest.approx(A4_H, abs=1)
    proc.close()
