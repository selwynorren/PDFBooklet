# src/gui/general_options_widget.py

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QComboBox,
    QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..logic.unit_converter import mm_to_inches, inches_to_mm
from .spinbox_buttons_widget import SpinboxButtonsWidget


class GeneralOptionsWidget(QWidget):
    # Define signals
    units_changed = pyqtSignal(str)
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.original_page_size = None  # (w_mm, h_mm) single page
        self.current_units = "mm"

        # Canonical custom size storage (always in mm)
        self._custom_size_mm = (0.0, 0.0)

        # --- Imposition Type Group ---
        self.imposition_type_group = QGroupBox(self.tr("Imposition Type"))
        imposition_type_layout = QVBoxLayout(self.imposition_type_group)

        # Combo items carry a stable logical value (userData) so program logic
        # never depends on the translated display text.
        self.imposition_type_combo = QComboBox()
        self.imposition_type_combo.addItem(self.tr("Booklet"), "booklet")
        self.imposition_type_combo.addItem(self.tr("Calendar"), "calendar")
        self.imposition_type_combo.addItem(self.tr("Single Page"), "single")
        imposition_type_layout.addWidget(self.imposition_type_combo)

        layout.addWidget(self.imposition_type_group)

        # --- Page Orientation Group ---
        self.orientation_group = QGroupBox(self.tr("Page Orientation"))
        orientation_layout = QVBoxLayout(self.orientation_group)

        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem(self.tr("Portrait"), "portrait")
        self.orientation_combo.addItem(self.tr("Landscape"), "landscape")
        self.orientation_combo.setCurrentIndex(0)  # Default to Landscape for booklets
        orientation_layout.addWidget(self.orientation_combo)

        self.orientation_combo.currentIndexChanged.connect(self.settings_changed.emit)

        layout.addWidget(self.orientation_group)

        # --- New Layout Group ---
        self.layout_group = QGroupBox(self.tr("Layout"))
        layout_group_layout = QVBoxLayout(self.layout_group)

        self.layout_combo = QComboBox()
        self.layout_combo.addItems(
            [
                self.tr("Single booklet"),
                self.tr("Multiple booklets"),
                self.tr("2 pages"),
                self.tr("x pages in line"),
                self.tr("x pages in columns"),
                self.tr("x copies"),
                self.tr("user defined"),
            ]
        )
        layout_group_layout.addWidget(self.layout_combo)

        layout.addWidget(self.layout_group)
        self.layout_group.setEnabled(False)

        # --- New Booklet Dimensions Group ---
        self.booklet_dimensions_group = QGroupBox(self.tr("Booklet Dimensions"))
        booklet_dimensions_layout = QGridLayout(self.booklet_dimensions_group)

        booklet_dimensions_layout.addWidget(QLabel(self.tr("Rows:")), 0, 0)
        self.rows_input = SpinboxButtonsWidget()
        self.rows_input.setSingleStep(1)
        self.rows_input.setRange(1, 99)
        self.rows_input.setValue(1)
        booklet_dimensions_layout.addWidget(self.rows_input, 0, 1)

        booklet_dimensions_layout.addWidget(QLabel(self.tr("Columns:")), 1, 0)
        self.columns_input = SpinboxButtonsWidget()
        self.columns_input.setSingleStep(1)
        self.columns_input.setRange(1, 99)
        self.columns_input.setValue(2)
        booklet_dimensions_layout.addWidget(self.columns_input, 1, 1)

        booklet_dimensions_layout.addWidget(QLabel(self.tr("Leafs:")), 2, 0)
        self.leafs_input = SpinboxButtonsWidget()
        self.leafs_input.setSingleStep(1)
        self.leafs_input.setRange(0, 99)
        booklet_dimensions_layout.addWidget(self.leafs_input, 2, 1)

        layout.addWidget(self.booklet_dimensions_group)
        self.booklet_dimensions_group.setEnabled(False)

        # --- Output Size Group ---
        self.output_size_group = QGroupBox(self.tr("Output Size"))
        # The selected size is the FINISHED (folded) page, not the printed sheet.
        # e.g. an A4 booklet folds two A5 pages onto an A3 sheet.
        self.output_size_group.setToolTip(
            self.tr(
                "This is the size of each finished, folded page — not the sheet you "
                "print on. A booklet folds two of these onto one sheet, so an A4 "
                "booklet prints on A3."
            )
        )
        output_size_layout = QGridLayout(self.output_size_group)

        self.output_size_combo = QComboBox()
        self.output_size_combo.addItem(self.tr("Automatic"), "automatic")
        self.output_size_combo.addItem("A4", "a4")
        self.output_size_combo.addItem("A3", "a3")
        self.output_size_combo.addItem(self.tr("Letter"), "letter")
        self.output_size_combo.addItem(self.tr("Legal"), "legal")
        self.output_size_combo.addItem(self.tr("Tabloid"), "tabloid")
        self.output_size_combo.addItem(self.tr("Custom"), "custom")
        output_size_layout.addWidget(self.output_size_combo, 0, 0, 1, 2)

        # Arranging custom size inputs vertically in the grid
        self.custom_width_label = QLabel(self.tr("Width:"))
        self.custom_width_input = SpinboxButtonsWidget()
        self.custom_width_input.setRange(0, 9999)
        self.custom_height_label = QLabel(self.tr("Height:"))
        self.custom_height_input = SpinboxButtonsWidget()
        self.custom_height_input.setRange(0, 9999)

        output_size_layout.addWidget(self.custom_width_label, 1, 0)
        output_size_layout.addWidget(self.custom_width_input, 1, 1)
        output_size_layout.addWidget(self.custom_height_label, 2, 0)
        output_size_layout.addWidget(self.custom_height_input, 2, 1)

        layout.addWidget(self.output_size_group)
        layout.addStretch()

        # Connect signals to emit settings_changed
        self.output_size_combo.currentIndexChanged.connect(self._update_custom_ui)
        self.output_size_combo.currentIndexChanged.connect(self.settings_changed.emit)
        self.custom_width_input.value_changed.connect(self._on_custom_inputs_changed)
        self.custom_height_input.value_changed.connect(self._on_custom_inputs_changed)

        self.rows_input.value_changed.connect(self.settings_changed.emit)
        self.columns_input.value_changed.connect(self.settings_changed.emit)
        self.leafs_input.value_changed.connect(self.settings_changed.emit)

        # Call update units on init to ensure suffix is set on load
        self.update_units(self.current_units)
        self._update_custom_ui()

    # ---------------------------
    # Public API
    # ---------------------------

    def set_enabled_state(self, enabled: bool):
        self.output_size_group.setEnabled(enabled)

    def set_original_page_size(self, size: tuple):
        self.original_page_size = size
        # Initialize custom size to spread dimensions in mm
        w_mm, h_mm = size
        self._custom_size_mm = (w_mm * 2, h_mm)

    def update_units(self, unit: str):
        """Update UI suffixes and refresh display values for the current mode."""
        self.current_units = unit

        # Only set the suffix on the SpinboxButtonsWidget
        self.custom_width_input.setSuffix(f" {unit}")
        self.custom_height_input.setSuffix(f" {unit}")

        self.units_changed.emit(unit)

        # Refresh display for current mode and unit
        self._refresh_inputs_for_current_mode()

    def get_unit(self) -> str:
        """Returns the currently selected unit (e.g., 'mm' or 'in')."""
        return self.current_units

    def get_imposition_mode(self) -> str:
        """
        Returns the selected imposition mode as a lowercase string:
        'booklet', 'calendar', or 'single'.
        """
        return self.imposition_type_combo.currentData()

    def get_output_size(self):
        """
        Returns the selected output size.
        """
        value = self.output_size_combo.currentData()
        if value == "automatic":
            return "automatic"
        elif value == "custom":
            return (
                self.custom_width_input.value(),
                self.custom_height_input.value(),
                self.current_units,
            )
        return value

    # ---------------------------
    # Internal UI logic
    # ---------------------------

    def _update_custom_ui(self):
        """Show/hide custom inputs and refresh values according to mode."""
        is_custom = self.output_size_combo.currentData() == "custom"
        self.custom_width_label.setVisible(is_custom)
        self.custom_width_input.setVisible(is_custom)
        self.custom_height_label.setVisible(is_custom)
        self.custom_height_input.setVisible(is_custom)

        self._refresh_inputs_for_current_mode()

    def _refresh_inputs_for_current_mode(self):
        """
        Updates the spinboxes to show correct values for the selected mode and units.
        - In Automatic or preset sizes: show computed spread in selected units.
        - In Custom: show self._custom_size_mm converted into selected units.
        Does not overwrite canonical mm storage.
        """
        value = self.output_size_combo.currentData()

        if value == "custom":
            # Convert canonical custom mm to display units
            w_mm, h_mm = self._custom_size_mm

            # Convert canonical custom mm to display units
            w_mm, h_mm = self._custom_size_mm
            if self.current_units == "in":
                w = round(mm_to_inches(w_mm), 2) if w_mm > 0 else 0.0
                h = round(mm_to_inches(h_mm), 2) if h_mm > 0 else 0.0
            else:
                w = round(w_mm, 2)
                h = round(h_mm, 2)
            self._set_spinboxes_blocked(w, h)
        else:
            # Automatic or named sizes — for simplicity, Automatic uses original_page_size doubled
            if not self.original_page_size:
                return

            single_w_mm, single_h_mm = self.original_page_size
            spread_w_mm = single_w_mm * 2
            spread_h_mm = single_h_mm

            if self.current_units == "in":
                w = round(mm_to_inches(spread_w_mm), 2)
                h = round(mm_to_inches(spread_h_mm), 2)
            else:
                w = round(spread_w_mm, 2)
                h = round(spread_h_mm, 2)
            self._set_spinboxes_blocked(w, h)

    def _on_custom_inputs_changed(self, _value):
        """
        When user edits custom width/height, update canonical mm storage.
        Only applies when 'Custom' is selected.
        """

        w = self.custom_width_input.value()
        h = self.custom_height_input.value()

        if self.current_units == "in":
            self._custom_size_mm = (
                round(inches_to_mm(w), 2),
                round(inches_to_mm(h), 2),
            )
        else:
            self._custom_size_mm = (round(w, 2), round(h, 2))

        # Emit after state update
        self.settings_changed.emit()

    def _set_spinboxes_blocked(self, w: float, h: float):
        """
        Set spinbox values while blocking signals to avoid triggering loops.
        """
        try:
            self.custom_width_input.blockSignals(True)
            self.custom_height_input.blockSignals(True)
            self.custom_width_input.setValue(w)
            self.custom_height_input.setValue(h)
        finally:
            self.custom_width_input.blockSignals(False)
            self.custom_height_input.blockSignals(False)

    def reset_imposition_mode(self):
        """
        Reset the imposition type combo box to default 'Booklet'.
        Call this when a new PDF is opened.
        """
        self.imposition_type_combo.setCurrentIndex(0)  # 0 = Booklet

    def get_orientation(self) -> str:
        """
        Returns the selected page orientation.

        Returns:
            'portrait' or 'landscape'
        """
        return self.orientation_combo.currentData()
