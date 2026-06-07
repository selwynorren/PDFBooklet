# PDFBooklet/tests/test_save_golden.py
"""
Golden / regression tests for the real save path (PDFSaver + BookletLayout).

Rather than byte-hashing output (brittle across pypdf versions — Phase 1 bumps
pypdf), these assert STRUCTURAL invariants of the produced PDF: page count and
per-page dimensions. That is the contract that must not regress through the
refactor and library bump.

Qt-free: drives PDFSaver and BookletLayout directly (neither imports PyQt6).
"""

import pytest
from pypdf import PdfReader

from src.logic.booklet_layout import BookletLayout
from src.logic.pdf_saver import PDFSaver
from src.logic.page_transforms import PageTransformManager, create_transform_from_gui

A5_W_PT = 148 * 72 / 25.4
A5_H_PT = 210 * 72 / 25.4


def _page_sizes(path):
    reader = PdfReader(path)
    return [(round(float(p.mediabox.width), 1), round(float(p.mediabox.height), 1))
            for p in reader.pages]


def test_booklet_save_structure(sample_pdf, tmp_path):
    out = str(tmp_path / "booklet.pdf")
    layout = BookletLayout(6)
    lmap = layout.generate_booklet_layout()
    sheet_w, sheet_h = A5_W_PT * 2, A5_H_PT  # booklet sheet = 2x wide

    ok, err = PDFSaver.save_booklet(
        sample_pdf, out, lmap, "booklet", sheet_w, sheet_h,
    )
    assert ok is True, err

    sizes = _page_sizes(out)
    assert len(sizes) == len(lmap)  # one sheet per spread (6 pads to 8 -> 4 spreads)
    for w, h in sizes:
        assert w == pytest.approx(sheet_w, abs=0.5)
        assert h == pytest.approx(sheet_h, abs=0.5)


def test_calendar_save_structure(sample_pdf, tmp_path):
    out = str(tmp_path / "calendar.pdf")
    layout = BookletLayout(6)
    lmap = layout.generate_calendar_layout()
    sheet_w, sheet_h = A5_W_PT, A5_H_PT * 2  # calendar sheet = 2x tall

    ok, err = PDFSaver.save_booklet(sample_pdf, out, lmap, "calendar", sheet_w, sheet_h)
    assert ok is True, err

    sizes = _page_sizes(out)
    assert len(sizes) == len(lmap)
    for w, h in sizes:
        assert w == pytest.approx(sheet_w, abs=0.5)
        assert h == pytest.approx(sheet_h, abs=0.5)


def test_single_save_structure(sample_pdf, tmp_path):
    out = str(tmp_path / "single.pdf")
    layout = BookletLayout(6)
    lmap = layout.generate_single_page_layout()

    ok, err = PDFSaver.save_booklet(sample_pdf, out, lmap, "single", A5_W_PT, A5_H_PT)
    assert ok is True, err

    sizes = _page_sizes(out)
    assert len(sizes) == 6
    for w, h in sizes:
        assert w == pytest.approx(A5_W_PT, abs=0.5)
        assert h == pytest.approx(A5_H_PT, abs=0.5)


def test_booklet_save_with_transforms_still_valid(sample_pdf, tmp_path):
    """A non-identity transform must still produce a structurally valid PDF."""
    out = str(tmp_path / "booklet_tf.pdf")
    layout = BookletLayout(4)
    lmap = layout.generate_booklet_layout()
    sheet_w, sheet_h = A5_W_PT * 2, A5_H_PT

    tm = PageTransformManager(4)
    tm.set_global_transform(
        create_transform_from_gui(h_shift_mm=5, scale_percent=90, rotation_deg=15)
    )

    ok, err = PDFSaver.save_booklet(
        sample_pdf, out, lmap, "booklet", sheet_w, sheet_h, transform_manager=tm,
    )
    assert ok is True, err
    sizes = _page_sizes(out)
    assert len(sizes) == len(lmap)
    for w, h in sizes:
        assert w == pytest.approx(sheet_w, abs=0.5)
        assert h == pytest.approx(sheet_h, abs=0.5)
