# PDFBooklet/tests/test_imposition.py
"""
Tests for the pure layout logic in src.logic.booklet_layout.

BookletLayout has no I/O, no rendering and no Qt dependency, so it is the
cheapest, highest-value place to lock down behaviour before refactoring.
"""

import pytest

from src.logic.booklet_layout import BookletLayout


# ----------------------------- Padding -----------------------------

@pytest.mark.parametrize(
    "count, expected_padding, expected_padded",
    [
        (4, 0, 4),
        (1, 3, 4),
        (2, 2, 4),
        (3, 1, 4),
        (5, 3, 8),
        (6, 2, 8),
        (8, 0, 8),
        (0, 0, 0),
    ],
)
def test_booklet_padding(count, expected_padding, expected_padded):
    layout = BookletLayout(count)
    assert layout.padding_needed == expected_padding
    assert layout.padded_page_count == expected_padded


# ----------------------------- Booklet -----------------------------

def test_booklet_layout_four_pages():
    """A 4-page doc folds into one sheet: front (3,0), back (1,2)."""
    layout = BookletLayout(4)
    result = layout.generate_booklet_layout()
    assert result == [(3, 0), (1, 2)]
    assert layout.active_mode == "booklet"


def test_booklet_layout_six_pages_pads_to_eight():
    """6 pages pad to 8; pages 6 and 7 are padding (blank)."""
    layout = BookletLayout(6)
    result = layout.generate_booklet_layout()
    assert result == [(7, 0), (1, 6), (5, 2), (3, 4)]
    # Every original page 0..5 appears exactly once across the spreads
    seen = sorted(idx for pair in result for idx in pair if idx < 6)
    assert seen == [0, 1, 2, 3, 4, 5]


def test_booklet_spreads_are_multiple_of_two():
    for count in range(1, 33):
        layout = BookletLayout(count)
        result = layout.generate_booklet_layout()
        # Two spreads (front + back) per physical sheet
        assert len(result) == layout.padded_page_count // 2


# ----------------------------- Calendar ----------------------------

def test_calendar_layout_even():
    layout = BookletLayout(4)
    result = layout.generate_calendar_layout()
    assert result == [(0, 1), (2, 3)]
    assert layout.active_mode == "calendar"


def test_calendar_layout_odd_has_trailing_blank():
    """Odd page count leaves a -1 (blank) in the final bottom slot."""
    layout = BookletLayout(3)
    result = layout.generate_calendar_layout()
    assert result == [(0, 1), (2, -1)]


# ------------------------------ Single -----------------------------

def test_single_page_layout():
    layout = BookletLayout(3)
    result = layout.generate_single_page_layout()
    assert result == [0, 1, 2]
    assert layout.active_mode == "single"


# --------------------------- Accessors -----------------------------

def test_get_page_indices_booklet():
    layout = BookletLayout(4)
    layout.generate_booklet_layout()
    assert layout.get_page_indices(0) == (3, 0)
    assert layout.get_page_indices(1) == (1, 2)


def test_get_page_indices_single_returns_blank_second():
    layout = BookletLayout(3)
    layout.generate_single_page_layout()
    assert layout.get_page_indices(1) == (1, -1)


def test_get_page_indices_out_of_range():
    layout = BookletLayout(4)
    layout.generate_booklet_layout()
    assert layout.get_page_indices(-1) == (-1, -1)
    assert layout.get_page_indices(99) == (-1, -1)


def test_get_layout_count():
    layout = BookletLayout(6)
    layout.generate_booklet_layout()
    assert layout.get_layout_count() == 4


def test_is_blank_page():
    layout = BookletLayout(6)  # pads to 8
    assert layout.is_blank_page(5) is False
    assert layout.is_blank_page(6) is True
    assert layout.is_blank_page(7) is True
