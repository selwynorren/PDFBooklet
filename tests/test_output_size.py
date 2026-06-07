# PDFBooklet/tests/test_output_size.py
"""
Characterization tests for output-size semantics.

DECISION (locked with the user): the selected output size is the FINISHED FOLDED
PAGE size, not the sheet. So in booklet mode the sheet is 2x wide; in calendar mode
2x tall. These tests pin that behavior so any accidental change is caught.

set_output_size is exercised on a real BookletProcessor (built from a fixture PDF).
The sheet-doubling in save_booklet is verified by capturing the dimensions handed to
PDFSaver (monkeypatched) — no actual file I/O needed.
"""

import pytest

from src.logic.booklet_processor import BookletProcessor
from src.logic import pdf_saver

MM_TO_PT = 72 / 25.4


def test_set_output_size_preset_a4(sample_pdf):
    proc = BookletProcessor(sample_pdf)
    proc.set_output_size("a4")
    assert proc.output_width == pytest.approx(210 * MM_TO_PT)
    assert proc.output_height == pytest.approx(297 * MM_TO_PT)
    proc.close()


def test_set_output_size_landscape_swaps(sample_pdf):
    proc = BookletProcessor(sample_pdf)
    proc.set_output_size("a4", orientation="landscape")
    assert proc.output_width == pytest.approx(297 * MM_TO_PT)
    assert proc.output_height == pytest.approx(210 * MM_TO_PT)
    proc.close()


def test_set_output_size_custom_inches(sample_pdf):
    proc = BookletProcessor(sample_pdf)
    proc.set_output_size((8.5, 11, "in"))
    assert proc.output_width == pytest.approx(8.5 * 72)
    assert proc.output_height == pytest.approx(11 * 72)
    proc.close()


def _capture_sheet_dims(proc, monkeypatch):
    """Run save_booklet but capture the dims passed to PDFSaver instead of saving."""
    captured = {}

    def fake_save(*args, **kwargs):
        captured["w"] = kwargs.get("output_width_pt", args[4] if len(args) > 4 else None)
        captured["h"] = kwargs.get("output_height_pt", args[5] if len(args) > 5 else None)
        return (True, None)

    monkeypatch.setattr(pdf_saver.PDFSaver, "save_booklet", staticmethod(fake_save))
    proc.save_booklet("/tmp/ignored.pdf", unit="mm")
    return captured


def test_booklet_sheet_is_double_width(sample_pdf, monkeypatch):
    proc = BookletProcessor(sample_pdf)
    proc.generate_booklet_layout(None, None)
    proc.set_output_size("a4")
    dims = _capture_sheet_dims(proc, monkeypatch)
    assert dims["w"] == pytest.approx(2 * 210 * MM_TO_PT)   # 2x wide
    assert dims["h"] == pytest.approx(297 * MM_TO_PT)       # height unchanged
    proc.close()


def test_calendar_sheet_is_double_height(sample_pdf, monkeypatch):
    proc = BookletProcessor(sample_pdf)
    proc.generate_calendar_layout(None, None)
    proc.set_output_size("a4")
    dims = _capture_sheet_dims(proc, monkeypatch)
    assert dims["w"] == pytest.approx(210 * MM_TO_PT)       # width unchanged
    assert dims["h"] == pytest.approx(2 * 297 * MM_TO_PT)   # 2x tall
    proc.close()


def test_single_sheet_is_not_doubled(sample_pdf, monkeypatch):
    proc = BookletProcessor(sample_pdf)
    proc.generate_single_page_layout(None, None)
    proc.set_output_size("a4")
    dims = _capture_sheet_dims(proc, monkeypatch)
    assert dims["w"] == pytest.approx(210 * MM_TO_PT)
    assert dims["h"] == pytest.approx(297 * MM_TO_PT)
    proc.close()
