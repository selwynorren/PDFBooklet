# PDFBooklet/tests/test_page_transforms.py
"""
Characterization tests for PageTransformManager.get_transform_for_page.

These lock in the CURRENT compounding rules before the Phase 2 refactor moves the
Transform model into src/data/. The rules (from page_transforms.py):
  - global is the base
  - even/odd domain and per-page each layer ON TOP, where:
      shifts ADD, scales MULTIPLY (value * other / 100),
      rotation ADDS, flips XOR.
  - "even/odd" is by 1-based page NUMBER: page_index 0 -> page_number 1 -> ODD.

No Qt, no I/O — pure logic.
"""

import pytest

from src.logic.page_transforms import (
    Transform,
    PageTransformManager,
    create_transform_from_gui,
)


def test_default_is_identity():
    mgr = PageTransformManager(4)
    assert mgr.get_transform_for_page(0) == Transform()
    assert mgr.get_transform_for_page(0).is_identity()


def test_out_of_range_returns_identity():
    mgr = PageTransformManager(4)
    assert mgr.get_transform_for_page(-1) == Transform()
    assert mgr.get_transform_for_page(99) == Transform()


def test_global_only_passes_through():
    mgr = PageTransformManager(4)
    mgr.set_global_transform(
        create_transform_from_gui(h_shift_mm=5, scale_percent=150, rotation_deg=10)
    )
    t = mgr.get_transform_for_page(2)
    assert t.h_shift_mm == 5
    assert t.scale_percent == 150
    assert t.rotation_deg == 10


def test_odd_domain_applies_to_page_index_zero():
    """page_index 0 is page_number 1 -> ODD domain applies; index 1 (even) does not."""
    mgr = PageTransformManager(4)
    mgr.set_page_transform(0, create_transform_from_gui(h_shift_mm=3), domain="odd")
    assert mgr.get_transform_for_page(0).h_shift_mm == 3   # index 0 = odd
    assert mgr.get_transform_for_page(1).h_shift_mm == 0   # index 1 = even


def test_even_domain_applies_to_page_index_one():
    mgr = PageTransformManager(4)
    mgr.set_page_transform(0, create_transform_from_gui(v_shift_mm=7), domain="even")
    assert mgr.get_transform_for_page(1).v_shift_mm == 7   # index 1 = even
    assert mgr.get_transform_for_page(0).v_shift_mm == 0   # index 0 = odd


def test_shifts_add_and_scales_multiply():
    mgr = PageTransformManager(4)
    mgr.set_global_transform(
        create_transform_from_gui(h_shift_mm=10, scale_percent=200)
    )
    # index 1 -> page_number 2 -> even
    mgr.set_page_transform(0, create_transform_from_gui(h_shift_mm=5, scale_percent=50), domain="even")
    t = mgr.get_transform_for_page(1)
    assert t.h_shift_mm == 15            # 10 + 5
    assert t.scale_percent == 100.0      # 200 * 50 / 100


def test_flips_xor():
    mgr = PageTransformManager(4)
    mgr.set_global_transform(create_transform_from_gui(h_flip=True))
    # per-page flip on the same page cancels the global flip (XOR)
    mgr.set_page_transform(2, create_transform_from_gui(h_flip=True), domain="this")
    assert mgr.get_transform_for_page(2).h_flip is False
    # a page without the per-page flip keeps the global flip
    assert mgr.get_transform_for_page(3).h_flip is True


def test_all_three_layers_compound():
    mgr = PageTransformManager(4)
    mgr.set_global_transform(create_transform_from_gui(h_shift_mm=1, rotation_deg=5))
    # index 1 = page_number 2 = even
    mgr.set_page_transform(0, create_transform_from_gui(h_shift_mm=2, rotation_deg=10), domain="even")
    mgr.set_page_transform(1, create_transform_from_gui(h_shift_mm=4, rotation_deg=20), domain="this")
    t = mgr.get_transform_for_page(1)
    assert t.h_shift_mm == 7        # 1 + 2 + 4
    assert t.rotation_deg == 35     # 5 + 10 + 20


def test_per_page_only_accessor():
    mgr = PageTransformManager(4)
    mgr.set_global_transform(create_transform_from_gui(h_shift_mm=99))
    mgr.set_page_transform(2, create_transform_from_gui(h_shift_mm=3), domain="this")
    # get_page_only_transform ignores global
    assert mgr.get_page_only_transform(2).h_shift_mm == 3
    assert mgr.get_page_only_transform(0).is_identity()


def test_has_any_transforms_and_reset():
    mgr = PageTransformManager(4)
    assert mgr.has_any_transforms() is False
    mgr.set_global_transform(create_transform_from_gui(h_shift_mm=1))
    assert mgr.has_any_transforms() is True
    mgr.reset()
    assert mgr.has_any_transforms() is False
    assert mgr.get_transform_for_page(0).is_identity()
