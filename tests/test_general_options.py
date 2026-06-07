# PDFBooklet/tests/test_general_options.py
"""
Tests that GeneralOptionsWidget's value getters return STABLE logical keys
(userData), independent of the combo boxes' translated display text. This guards
the i18n refactor: translating the UI must not change program behavior.
"""

import pytest

from src.gui.general_options_widget import GeneralOptionsWidget


@pytest.fixture
def widget(qapp):
    w = GeneralOptionsWidget()
    yield w
    w.deleteLater()


def test_imposition_mode_keys(widget):
    for index, expected in enumerate(["booklet", "calendar", "single"]):
        widget.imposition_type_combo.setCurrentIndex(index)
        assert widget.get_imposition_mode() == expected


def test_orientation_keys(widget):
    widget.orientation_combo.setCurrentIndex(0)
    assert widget.get_orientation() == "portrait"
    widget.orientation_combo.setCurrentIndex(1)
    assert widget.get_orientation() == "landscape"


def test_output_size_preset_keys(widget):
    expected = ["automatic", "a4", "a3", "letter", "legal", "tabloid"]
    for index, key in enumerate(expected):
        widget.output_size_combo.setCurrentIndex(index)
        assert widget.get_output_size() == key


def test_output_size_custom_returns_tuple(widget):
    # last item is Custom
    widget.output_size_combo.setCurrentIndex(widget.output_size_combo.count() - 1)
    result = widget.get_output_size()
    assert isinstance(result, tuple) and len(result) == 3
    assert result[2] in ("mm", "in")
