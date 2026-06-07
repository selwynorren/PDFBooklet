# PDFBooklet/tests/conftest.py
"""
Shared pytest fixtures.

These fixtures generate small, deterministic PDFs at test time (via PyMuPDF) so
the regression tests need no committed binary fixtures and no display/Qt.
"""

import os

# Some tests construct a BookletProcessor (which builds a Qt-backed renderer).
# Default to the offscreen platform so the suite runs without a display (CI).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz  # PyMuPDF
import pytest

# A5 portrait in points (148 x 210 mm). Chosen so a booklet sheet (2x wide)
# lands near A4 landscape — realistic, and easy to assert against.
A5_W_PT = 148 * 72 / 25.4
A5_H_PT = 210 * 72 / 25.4


def _make_pdf(path, page_count, width_pt=A5_W_PT, height_pt=A5_H_PT):
    """Create a PDF with `page_count` numbered pages of the given size."""
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page(width=width_pt, height=height_pt)
        page.insert_text((72, 72), f"Page {i + 1}")
    doc.save(str(path))
    doc.close()


@pytest.fixture(scope="session")
def qapp():
    """A single QApplication for widget tests (offscreen)."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def sample_pdf(tmp_path):
    """A 6-page A5 PDF. 6 pads to 8 in booklet mode (exercises blank padding)."""
    path = tmp_path / "sample_6.pdf"
    _make_pdf(path, 6)
    return str(path)


@pytest.fixture
def make_pdf(tmp_path):
    """Factory: make_pdf(page_count) -> path to a fresh A5 PDF."""
    def _factory(page_count):
        path = tmp_path / f"sample_{page_count}.pdf"
        _make_pdf(path, page_count)
        return str(path)
    return _factory
