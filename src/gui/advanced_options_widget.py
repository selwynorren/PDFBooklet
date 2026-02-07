# PDFBooklet/src/gui/advanced_options_widget.py
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QLocale, pyqtSignal as Signal
from .spinbox_buttons_widget import SpinboxButtonsWidget


class AdvancedOptionsWidget(QWidget):
    units_changed = Signal(str)
    settings_changed = Signal()  # For all advanced options EXCEPT preview_dpi_combo
    locale_changed = Signal(str)  # New signal for app-level locale override

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Units Group ---
        self.units_group = QGroupBox("Units")
        units_layout = QGridLayout(self.units_group)

        units_layout.addWidget(QLabel("Dimension Units:"), 0, 0)
        self.units_combo = QComboBox()
        self.units_combo.addItems(["mm", "in"])
        units_layout.addWidget(self.units_combo, 0, 1)

        layout.addWidget(self.units_group)

        # --- Locale Group ---
        self.locale_group = QGroupBox("Locale")
        locale_layout = QGridLayout(self.locale_group)

        locale_layout.addWidget(QLabel("App Locale:"), 0, 0)
        self.locale_combo = QComboBox()
        # Curated list of common locales
        self.locale_combo.addItems(
            [
                "System Default",
                "English (United States)",
                "English (United Kingdom)",
                "English (South Africa)",
                "French (France)",
                "German (Germany)",
                "Chinese (China)",
                "Russian (Russia)",
                "Japanese (Japan)",
            ]
        )
        self.locale_combo.setCurrentIndex(0)
        locale_layout.addWidget(self.locale_combo, 0, 1)

        layout.addWidget(self.locale_group)

        # --- Resolution Group ---
        self.resolution_group = QGroupBox("Resolution")
        resolution_layout = QGridLayout(self.resolution_group)

        resolution_layout.addWidget(QLabel("Preview DPI:"), 0, 0)
        self.preview_dpi_combo = QComboBox()
        self.preview_dpi_combo.addItems(["72", "96", "150", "300", "600"])
        self.preview_dpi_combo.setCurrentIndex(0)  # Always start at 72
        resolution_layout.addWidget(self.preview_dpi_combo, 0, 1)

        # Save DPI controls
        self.save_dpi_label = QLabel("Downscaled Save DPI:")
        resolution_layout.addWidget(self.save_dpi_label, 1, 0)

        self.save_dpi_combo = QComboBox()
        self.save_dpi_combo.addItems(["72", "96", "150", "300", "600", "1200"])
        self.save_dpi_combo.setCurrentIndex(1)  # Default to 300
        resolution_layout.addWidget(self.save_dpi_combo, 1, 1)

        self.downscale_checkbox = QCheckBox("Downscale Images on Save")
        resolution_layout.addWidget(self.downscale_checkbox, 2, 0, 1, 2)

        layout.addWidget(self.resolution_group)

        # --- Save Options Group ---
        self.save_group = QGroupBox("Save Options")
        save_layout = QGridLayout(self.save_group)

        save_layout.addWidget(QLabel("Filename Suffix:"), 0, 0)
        self.suffix_input = QLineEdit("-bklt")
        self.suffix_input.setMinimumWidth(100)
        save_layout.addWidget(self.suffix_input, 0, 1)

        layout.addWidget(self.save_group)

        # --- Booklet Options Group ---
        self.booklet_options_group = QGroupBox("Booklet Options")
        booklet_options_layout = QGridLayout(self.booklet_options_group)

        booklet_options_layout.addWidget(QLabel("Creep:"), 0, 0)
        self.creep_input = SpinboxButtonsWidget()
        self.creep_input.setSuffix(" mm")
        self.creep_input.setRange(0, 99)
        self.creep_input.setSingleStep(1)
        booklet_options_layout.addWidget(self.creep_input, 0, 1)

        booklet_options_layout.addWidget(QLabel("Leading Blank Pages:"), 1, 0)
        self.leading_blanks_input = SpinboxButtonsWidget()
        self.leading_blanks_input.setRange(0, 99)
        self.leading_blanks_input.setSingleStep(1)
        booklet_options_layout.addWidget(self.leading_blanks_input, 1, 1)

        booklet_options_layout.addWidget(QLabel("Trailing Blank Pages:"), 2, 0)
        self.trailing_blanks_input = SpinboxButtonsWidget()
        self.trailing_blanks_input.setRange(0, 99)
        self.trailing_blanks_input.setSingleStep(1)
        booklet_options_layout.addWidget(self.trailing_blanks_input, 2, 1)

        layout.addWidget(self.booklet_options_group)
        layout.addStretch()

        # --- Connections ---
        self.units_combo.currentIndexChanged.connect(self._on_settings_changed)
        self.save_dpi_combo.currentIndexChanged.connect(self._on_settings_changed)
        self.suffix_input.textChanged.connect(self._on_settings_changed)
        self.downscale_checkbox.stateChanged.connect(self._on_settings_changed)
        self.units_combo.currentIndexChanged.connect(self._on_units_changed)
        self.downscale_checkbox.stateChanged.connect(self._update_save_dpi_state)
        self.locale_combo.currentIndexChanged.connect(self._on_locale_changed)

        self._update_save_dpi_state()

        # Keep booklet options permanently disabled
        self.booklet_options_group.setEnabled(False)

    # -------------------------
    # Public API
    # -------------------------
    def reset_preview_dpi(self):
        """Reset Preview DPI combo box to default (72 DPI)."""
        self.preview_dpi_combo.blockSignals(True)
        self.preview_dpi_combo.setCurrentIndex(0)
        self.preview_dpi_combo.blockSignals(False)

    def get_preview_dpi(self) -> int:
        """Return current Preview DPI as int (runtime only)."""
        return int(self.preview_dpi_combo.currentText())

    def get_suffix(self) -> str:
        """Returns the current filename suffix."""
        return self.suffix_input.text().strip()

    def get_unit(self) -> str:
        """Returns the currently selected unit ('mm' or 'in')."""
        return self.units_combo.currentText()

    def get_save_dpi(self) -> int:
        """Returns the selected save DPI as an integer."""
        return int(self.save_dpi_combo.currentText())

    def should_downscale_images(self) -> bool:
        """Returns True if downscaling is enabled."""
        return self.downscale_checkbox.isChecked()

    def get_locale(self) -> str:
        """Returns the selected app-level locale string."""
        return self.locale_combo.currentText()

    def get_options(self):
        return {
            "units": self.units_combo.currentText(),
            "suffix": self.suffix_input.text(),
            "creep": self.creep_input.value(),
            "leading_blanks": self.leading_blanks_input.value(),
            "trailing_blanks": self.trailing_blanks_input.value(),
            "locale": self.locale_combo.currentText(),
            "downscale": self.should_downscale_images(),
            "target_dpi": self.get_save_dpi(),
        }

    def set_options(self, settings):
        index = self.units_combo.findText(settings.get("units", "mm"))
        if index != -1:
            self.units_combo.setCurrentIndex(index)

        self.reset_preview_dpi()
        self.suffix_input.setText(settings.get("suffix", "-bklt"))
        self.creep_input.setValue(settings.get("creep", 0))
        self.leading_blanks_input.setValue(settings.get("leading_blanks", 0))
        self.trailing_blanks_input.setValue(settings.get("trailing_blanks", 0))

        locale_index = self.locale_combo.findText(
            settings.get("locale", "System Default")
        )
        if locale_index != -1:
            self.locale_combo.setCurrentIndex(locale_index)
            # Apply locale immediately when restoring
            self._on_locale_changed()

    def reset_downscale_settings(self):
        """Reset downscale checkbox and DPI combo to defaults."""
        self.downscale_checkbox.setChecked(False)
        self.save_dpi_combo.setCurrentIndex(3)  # Default to 300
        self._update_save_dpi_state()

    # -------------------------
    # Internal slots
    # -------------------------
    def _on_settings_changed(self):
        self.settings_changed.emit()

    def _on_units_changed(self):
        self.units_changed.emit(self.units_combo.currentText())

    def _on_locale_changed(self):
        locale_string = self.locale_combo.currentText()
        if locale_string == "System Default":
            locale = QLocale.system()
        elif locale_string == "English (United States)":
            locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        elif locale_string == "English (United Kingdom)":
            locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom)
        elif locale_string == "English (South Africa)":
            locale = QLocale(QLocale.Language.English, QLocale.Country.SouthAfrica)
        elif locale_string == "French (France)":
            locale = QLocale(QLocale.Language.French, QLocale.Country.France)
        elif locale_string == "German (Germany)":
            locale = QLocale(QLocale.Language.German, QLocale.Country.Germany)
        elif locale_string == "Chinese (China)":
            locale = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
        elif locale_string == "Russian (Russia)":
            locale = QLocale(QLocale.Language.Russian, QLocale.Country.Russia)
        elif locale_string == "Japanese (Japan)":
            locale = QLocale(QLocale.Language.Japanese, QLocale.Country.Japan)
        else:
            locale = QLocale.system()

        for sb in (
            self.creep_input.spinbox,
            self.leading_blanks_input.spinbox,
            self.trailing_blanks_input.spinbox,
        ):
            sb.setLocale(locale)
            sb.lineEdit().setLocale(locale)

            # Intercept text edits to normalize decimal separator
            def normalize(text, spinbox=sb, loc=locale):
                sep = loc.decimalPoint()
                if sep == "," and "." in text:
                    spinbox.lineEdit().setText(text.replace(".", ","))
                elif sep == "." and "," in text:
                    spinbox.lineEdit().setText(text.replace(",", "."))

            sb.lineEdit().textEdited.connect(normalize)

        self.locale_changed.emit(locale_string)

    def _update_save_dpi_state(self):
        is_checked = self.downscale_checkbox.isChecked()
        self.save_dpi_combo.setEnabled(is_checked)
        self.save_dpi_label.setEnabled(is_checked)

    def update_units(self, unit: str):
        self.current_units = unit
        self.creep_input.setSuffix(f" {unit}")
        self.leading_blanks_input.setSuffix(f" {unit}")
        self.trailing_blanks_input.setSuffix(f" {unit}")
        self.booklet_options_group.setTitle(f"Booklet Options ({unit})")

    def _update_save_dpi_state(self):
        is_checked = self.downscale_checkbox.isChecked()
        self.save_dpi_combo.setEnabled(is_checked)
        self.save_dpi_label.setEnabled(is_checked)
