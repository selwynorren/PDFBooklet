# pdfbooklet/gui/page_options_widget.py
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QRadioButton,
    QLabel,
    QDoubleSpinBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..logic.unit_converter import mm_to_inches, inches_to_mm
from .spinbox_buttons_widget import SpinboxButtonsWidget


class PageOptionsWidget(QWidget):
    # Define signals
    units_changed = pyqtSignal(str)
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Domain Group ---
        self.domain_group = QGroupBox("Domain")
        domain_layout = QVBoxLayout(self.domain_group)
        # self.domain_all = QRadioButton("All pages in this position")
        # self.domain_all.setChecked(True)
        self.domain_this = QRadioButton("Selected page only")
        self.domain_even = QRadioButton("All even pages")
        self.domain_odd = QRadioButton("All odd pages")
        # domain_layout.addWidget(self.domain_all)
        domain_layout.addWidget(self.domain_this)
        domain_layout.addWidget(self.domain_even)
        domain_layout.addWidget(self.domain_odd)
        layout.addWidget(self.domain_group)

        # --- Transformations Group ---
        self.transformations_group = QGroupBox("Transformations")
        transformations_layout = QGridLayout(self.transformations_group)

        transformations_layout.addWidget(QLabel("Horizontal Shift:"), 0, 0)
        self.h_shift_input = SpinboxButtonsWidget()
        self.h_shift_input.setSingleStep(1)
        self.h_shift_input.setRange(-999, 999)
        transformations_layout.addWidget(self.h_shift_input, 0, 1)

        transformations_layout.addWidget(QLabel("Vertical Shift:"), 1, 0)
        self.v_shift_input = SpinboxButtonsWidget()
        self.v_shift_input.setSingleStep(1)
        self.v_shift_input.setRange(-999, 999)
        transformations_layout.addWidget(self.v_shift_input, 1, 1)

        transformations_layout.addWidget(QLabel("Scale (%):"), 2, 0)
        self.scale_input = SpinboxButtonsWidget()
        self.scale_input.setSuffix(" %")
        self.scale_input.setRange(0, 999)
        self.scale_input.setValue(100)
        self.scale_input.setSingleStep(1)
        transformations_layout.addWidget(self.scale_input, 2, 1)

        transformations_layout.addWidget(QLabel("Rotation (°):"), 3, 0)
        self.rotation_input = SpinboxButtonsWidget()
        self.rotation_input.setSuffix(" °")
        self.rotation_input.setRange(-360, 360)
        self.rotation_input.setSingleStep(1)
        transformations_layout.addWidget(self.rotation_input, 3, 1)

        transformations_layout.addWidget(QLabel("Horizontal Flip:"), 4, 0)
        self.h_flip_checkbox = QCheckBox()
        transformations_layout.addWidget(self.h_flip_checkbox, 4, 1)

        transformations_layout.addWidget(QLabel("Vertical Flip:"), 5, 0)
        self.v_flip_checkbox = QCheckBox()
        transformations_layout.addWidget(self.v_flip_checkbox, 5, 1)

        transformations_layout.addWidget(QLabel("Scale Horizontally (%):"), 6, 0)
        self.h_scale_input = SpinboxButtonsWidget()
        self.h_scale_input.setSuffix(" %")
        self.h_scale_input.setRange(0, 999)
        self.h_scale_input.setValue(100)
        self.h_scale_input.setSingleStep(1)
        transformations_layout.addWidget(self.h_scale_input, 6, 1)

        transformations_layout.addWidget(QLabel("Scale Vertically (%):"), 7, 0)
        self.v_scale_input = SpinboxButtonsWidget()
        self.v_scale_input.setSuffix(" %")
        self.v_scale_input.setRange(0, 999)
        self.v_scale_input.setValue(100)
        self.v_scale_input.setSingleStep(1)
        transformations_layout.addWidget(self.v_scale_input, 7, 1)

        layout.addWidget(self.transformations_group)
        layout.addStretch()

        self.h_shift_input.value_changed.connect(self.settings_changed.emit)
        self.v_shift_input.value_changed.connect(self.settings_changed.emit)
        self.scale_input.value_changed.connect(self.settings_changed.emit)
        self.rotation_input.value_changed.connect(self.settings_changed.emit)

    def set_enabled_state(self, enabled: bool):
        self.domain_group.setEnabled(enabled)
        self.transformations_group.setEnabled(enabled)
        # Manually set the enabled state for the new widgets
        self.h_shift_input.set_enabled_state(enabled)
        self.v_shift_input.set_enabled_state(enabled)
        self.scale_input.set_enabled_state(enabled)
        self.rotation_input.set_enabled_state(enabled)
        self.h_scale_input.set_enabled_state(enabled)
        self.v_scale_input.set_enabled_state(enabled)

    def update_units(self, unit: str):
        # Update the labels
        self.transformations_group.setTitle(f"Transformations ({unit})")

        # Update all spinboxes
        self.h_shift_input.update_units(unit)
        self.v_shift_input.update_units(unit)
        # self.scale_input.update_units(unit)
        # self.rotation_input.update_units(unit)
        # self.h_scale_input.update_units(unit)
        # self.v_scale_input.update_units(unit)

        # Emit signal
        self.units_changed.emit(unit)

    def get_transformations(self) -> dict:
        """Get current transformation values."""
        return {
            "h_shift_mm": self.h_shift_input.value(),
            "v_shift_mm": self.v_shift_input.value(),
            "scale_percent": self.scale_input.value(),
            "rotation_deg": self.rotation_input.value(),
            "h_flip": self.h_flip_checkbox.isChecked(),
            "v_flip": self.v_flip_checkbox.isChecked(),
            "h_scale_percent": self.h_scale_input.value(),
            "v_scale_percent": self.v_scale_input.value(),
        }

    def set_transformations(self, transform_dict: dict):
        """Set transformation values from a dictionary."""
        self.h_shift_input.setValue(transform_dict.get("h_shift_mm", 0.0))
        self.v_shift_input.setValue(transform_dict.get("v_shift_mm", 0.0))
        self.scale_input.setValue(transform_dict.get("scale_percent", 100.0))
        self.rotation_input.setValue(transform_dict.get("rotation_deg", 0.0))
        self.h_flip_checkbox.setChecked(transform_dict.get("h_flip", False))
        self.v_flip_checkbox.setChecked(transform_dict.get("v_flip", False))
        self.h_scale_input.setValue(transform_dict.get("h_scale_percent", 100.0))
        self.v_scale_input.setValue(transform_dict.get("v_scale_percent", 100.0))

    def get_domain(self) -> str:
        """Get selected domain."""
        if self.domain_this.isChecked():
            return "this"
        elif self.domain_even.isChecked():
            return "even"
        elif self.domain_odd.isChecked():
            return "odd"
        return "this"
