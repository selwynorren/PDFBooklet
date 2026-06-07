# PDFBooklet/src/data/settings_store.py
"""
Persistent application settings.

Wraps QSettings so the GUI never deals with storage keys, defaults, or value
typing directly. QSettings is a Qt class, but persistence is a data concern — this
is the one place that knows how/where state is stored.

Storage layout (unchanged from prior in-GUI usage, for backward compatibility):
  window/geometry            -> QByteArray (saveGeometry/restoreGeometry blob)
  last_dir                   -> str (last file dialog directory)
  advanced_options/<key>     -> typed advanced-options values
"""

from PyQt6.QtCore import QSettings, QByteArray

# Advanced options: key -> (default, type). Loaded as a typed group.
_ADVANCED_DEFAULTS = {
    "units": ("mm", str),
    "suffix": ("-bklt", str),
    "creep": (0, int),
    "leading_blanks": (0, int),
    "trailing_blanks": (0, int),
    "locale": ("System Default", str),
}


class SettingsStore:
    """Typed accessors over QSettings('PDFBooklet', 'PDFBooklet')."""

    ORGANIZATION = "PDFBooklet"
    APPLICATION = "PDFBooklet"

    def __init__(self, settings: QSettings | None = None):
        # Allow injecting a QSettings (e.g. for tests); default to the app's store.
        self._settings = settings or QSettings(self.ORGANIZATION, self.APPLICATION)

    # ---- window geometry ----
    def has_window_geometry(self) -> bool:
        return self._settings.contains("window/geometry")

    def get_window_geometry(self) -> QByteArray:
        return self._settings.value("window/geometry", QByteArray())

    def set_window_geometry(self, data: QByteArray) -> None:
        self._settings.setValue("window/geometry", data)

    # ---- last directory ----
    def get_last_dir(self) -> str:
        return self._settings.value("last_dir", "")

    def set_last_dir(self, path: str) -> None:
        self._settings.setValue("last_dir", path)

    # ---- advanced options (typed group) ----
    def get_advanced_options(self) -> dict:
        return {
            key: self._settings.value(f"advanced_options/{key}", default, type=typ)
            for key, (default, typ) in _ADVANCED_DEFAULTS.items()
        }

    def set_advanced_options(self, options: dict) -> None:
        for key, value in options.items():
            self._settings.setValue(f"advanced_options/{key}", value)
