# pdfbooklet/gui/spinbox_buttons_widget.py
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QAbstractSpinBox,
    QApplication,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal as Signal, QLocale
from PyQt6.QtGui import QValidator

from ..logic.unit_converter import mm_to_inches, inches_to_mm


class LocaleAwareDoubleSpinBox(QDoubleSpinBox):
    """
    Accepts both '.' and ',' for input; formats output strictly by the current QLocale.
    Disables group separators to avoid locale bleed-through.
    Ensures typed values commit correctly on Enter.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._locale = QLocale.system()
        self.setGroupSeparatorShown(False)
        if self.lineEdit():
            self.lineEdit().setLocale(self._locale)
            # Ensure typed values commit
            self.lineEdit().editingFinished.connect(self._commit_text)

    def setLocale(self, locale: QLocale):
        self._locale = locale
        super().setLocale(locale)
        if self.lineEdit():
            self.lineEdit().setLocale(locale)

    def valueFromText(self, text: str) -> float:
        sep = self._locale.decimalPoint()
        if sep == ",":
            normalized = text.replace(".", ",")
        else:
            normalized = text.replace(",", ".")
        value, ok = self._locale.toDouble(normalized)
        if ok:
            return value
        try:
            return float(normalized.replace(",", "."))
        except ValueError:
            return self.value()

    def textFromValue(self, value: float) -> str:
        decimals = self.decimals()
        text = self._locale.toString(value, "f", decimals)
        if self._locale.groupSeparator() in text:
            text = text.replace(self._locale.groupSeparator(), "")
        return text

    def _commit_text(self):
        """
        Force commit of the current line edit text into the spinbox value.
        This ensures typed numbers like '200' stick after pressing Enter.
        """
        text = self.lineEdit().text().strip()
        # Remove suffix if present
        suffix = self.suffix()
        if suffix and text.endswith(suffix):
            text = text[: -len(suffix)].strip()

        try:
            new_val = self.valueFromText(text)
            self.setValue(new_val)
        except Exception as e:
            pass  # Silently ignore parsing errors

    def keyPressEvent(self, event):
        """Handle Enter/Return key to properly commit typed values."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Manually parse and set the typed value
            text = self.lineEdit().text().strip()
            suffix = self.suffix()
            if suffix and text.endswith(suffix):
                text = text[: -len(suffix)].strip()

            try:
                new_val = self.valueFromText(text)
                self.setValue(new_val)
                self.clearFocus()  # Trigger editingFinished
            except:
                pass
            event.accept()
        else:
            super().keyPressEvent(event)


class SpinboxButtonsWidget(QWidget):
    value_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._min_value_mm = -9999
        self._max_value_mm = 9999
        self._step_mm = 1.0
        self._unit = "mm"

        # Use locale‑aware spinbox
        self.spinbox = LocaleAwareDoubleSpinBox()
        self.spinbox.setDecimals(2)
        self.spinbox.setMinimumWidth(80)
        self.spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.up_button = QPushButton("+")
        self.down_button = QPushButton("-")
        self.up_button.setFixedWidth(20)
        self.down_button.setFixedWidth(20)

        # Enable auto-repeat on hold
        self.up_button.setAutoRepeat(True)
        self.down_button.setAutoRepeat(True)
        self.up_button.setAutoRepeatDelay(
            300
        )  # Initial delay in ms before repeat starts
        self.down_button.setAutoRepeatDelay(300)
        self.up_button.setAutoRepeatInterval(50)  # Interval in ms between repeats
        self.down_button.setAutoRepeatInterval(50)

        layout.addWidget(self.spinbox)
        layout.addWidget(self.down_button)
        layout.addWidget(self.up_button)

        # Connections
        self.up_button.clicked.connect(self._increment_value)
        self.down_button.clicked.connect(self._decrement_value)
        self.spinbox.valueChanged.connect(self._on_spinbox_value_changed)

    def _increment_value(self):
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            step = round(self._step_mm / 10.0, 2)
        else:
            step = self._step_mm
        self.spinbox.setValue(self.spinbox.value() + step)

    def _decrement_value(self):
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            step = round(self._step_mm / 10.0, 2)
        else:
            step = self._step_mm
        self.spinbox.setValue(self.spinbox.value() - step)

    def _on_spinbox_value_changed(self, value):
        if self._unit == "in":
            mm_value = inches_to_mm(value)
        else:
            mm_value = value
        self.value_changed.emit(mm_value)

    def setRange(self, min_val, max_val):
        self._min_value_mm = min_val
        self._max_value_mm = max_val
        self.spinbox.setRange(min_val, max_val)

    def setSingleStep(self, step):
        self._step_mm = step
        self.spinbox.setSingleStep(step)

    def setSuffix(self, suffix: str):
        self.spinbox.setSuffix(suffix)

    def setValue(self, value_mm: float):
        if self._unit == "in":
            display_value = mm_to_inches(value_mm)
        else:
            display_value = value_mm
        self.spinbox.setValue(display_value)

    def value(self):
        if self._unit == "in":
            return inches_to_mm(self.spinbox.value())
        return self.spinbox.value()

    def set_enabled_state(self, enabled: bool):
        self.setEnabled(enabled)

    def update_units(self, unit: str):
        self._unit = unit
        if unit == "in":
            self.setSuffix(" in")
            self.spinbox.setRange(
                mm_to_inches(self._min_value_mm), mm_to_inches(self._max_value_mm)
            )
            self.spinbox.setSingleStep(mm_to_inches(self._step_mm))
        else:  # "mm"
            self.setSuffix(" mm")
            self.spinbox.setRange(self._min_value_mm, self._max_value_mm)
            self.spinbox.setSingleStep(self._step_mm)

        self.setValue(self.value())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self._increment_value()
        elif event.key() == Qt.Key.Key_Down:
            self._decrement_value()
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Plus:
                self._increment_value()
            elif event.key() == Qt.Key.Key_Minus:
                self._decrement_value()
        else:
            super().keyPressEvent(event)
