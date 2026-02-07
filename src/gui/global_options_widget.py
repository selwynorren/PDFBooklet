# PDFBooklet/src/gui/global_options_widget.py

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QCheckBox,
)
from PyQt6.QtCore import pyqtSignal

from .spinbox_buttons_widget import SpinboxButtonsWidget


class GlobalOptionsWidget(QWidget):
    units_changed = pyqtSignal(str)
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Global Transformations Group ---
        self.transformations_group = QGroupBox("Global Transformations")
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

    def set_enabled_state(self, enabled: bool):
        self.transformations_group.setEnabled(enabled)
        self.h_shift_input.set_enabled_state(enabled)
        self.v_shift_input.set_enabled_state(enabled)
        self.scale_input.set_enabled_state(enabled)
        self.rotation_input.set_enabled_state(enabled)
        self.h_scale_input.set_enabled_state(enabled)
        self.v_scale_input.set_enabled_state(enabled)

    def update_units(self, unit: str):
        self.transformations_group.setTitle(f"Global Transformations ({unit})")
        self.h_shift_input.update_units(unit)
        self.v_shift_input.update_units(unit)
        self.units_changed.emit(unit)

    def get_domain(self) -> str:
        """
        Get the selected domain.

        Returns:
            One of: 'this', 'all', 'even', 'odd'
        """
        if self.domain_this.isChecked():
            return "this"
        elif self.domain_all.isChecked():
            return "all"
        elif self.domain_even.isChecked():
            return "even"
        elif self.domain_odd.isChecked():
            return "odd"
        return "this"  # Default

    def get_transformations(self) -> dict:
        """
        Get all current transformation values.

        Returns:
            Dictionary with all transformation parameters in mm and raw values
        """
        return {
            "h_shift_mm": self.h_shift_input.value(),  # Already in mm
            "v_shift_mm": self.v_shift_input.value(),  # Already in mm
            "scale_percent": self.scale_input.value(),  # Percentage
            "rotation_deg": self.rotation_input.value(),  # Degrees
            "h_flip": self.h_flip_checkbox.isChecked(),  # Boolean
            "v_flip": self.v_flip_checkbox.isChecked(),  # Boolean
            "h_scale_percent": self.h_scale_input.value(),  # Percentage
            "v_scale_percent": self.v_scale_input.value(),  # Percentage
        }
