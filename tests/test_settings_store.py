# PDFBooklet/tests/test_settings_store.py
"""
Tests for the data-tier SettingsStore. Uses an injected file-backed QSettings so
nothing touches the real user config.
"""

from PyQt6.QtCore import QSettings

from src.data.settings_store import SettingsStore


def _store(tmp_path):
    qs = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return SettingsStore(qs)


def test_advanced_options_defaults(tmp_path):
    store = _store(tmp_path)
    opts = store.get_advanced_options()
    assert opts == {
        "units": "mm",
        "suffix": "-bklt",
        "creep": 0,
        "leading_blanks": 0,
        "trailing_blanks": 0,
        "locale": "System Default",
    }


def test_advanced_options_round_trip_with_types(tmp_path):
    store = _store(tmp_path)
    store.set_advanced_options(
        {
            "units": "in",
            "suffix": "-book",
            "creep": 3,
            "leading_blanks": 2,
            "trailing_blanks": 1,
            "locale": "English (United Kingdom)",
        }
    )
    opts = SettingsStore(
        QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ).get_advanced_options()
    assert opts["units"] == "in"
    assert opts["creep"] == 3 and isinstance(opts["creep"], int)
    assert opts["locale"] == "English (United Kingdom)"


def test_last_dir_round_trip(tmp_path):
    store = _store(tmp_path)
    assert store.get_last_dir() == ""
    store.set_last_dir("/home/user/pdfs")
    assert store.get_last_dir() == "/home/user/pdfs"


def test_window_geometry_presence(tmp_path):
    store = _store(tmp_path)
    assert store.has_window_geometry() is False
    store.set_window_geometry(b"\x01\x02\x03")
    assert store.has_window_geometry() is True
