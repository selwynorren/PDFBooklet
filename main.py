# PDFBooklet/src/main.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTranslator, QLocale

# This line ensures that Python finds the modules in the src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set the application's organization and name for QSettings
QApplication.setOrganizationName("PdfBooklet")
QApplication.setApplicationName("PDF Booklet")

from src.gui.main_window import MainWindow

# Directory holding compiled .qm translation files (see docs/TRANSLATING.md).
I18N_DIR = os.path.join(os.path.dirname(__file__), "src", "assets", "i18n")


def install_translator(app: QApplication) -> QTranslator:
    """
    Load and install the best-matching UI translation for the current locale.

    Looks for src/assets/i18n/pdfbooklet_<locale>.qm. If none is found the app
    falls back to the English source strings, so this never fails the user.
    The returned translator must be kept alive for the app's lifetime.
    """
    translator = QTranslator()
    # QLocale() uses the system UI languages; load() picks the best match,
    # e.g. pdfbooklet_af.qm for Afrikaans, pdfbooklet_fr.qm for French.
    if translator.load(QLocale(), "pdfbooklet", "_", I18N_DIR, ".qm"):
        app.installTranslator(translator)
    return translator


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Install translations before building the UI so wrapped strings are localized.
    _translator = install_translator(app)

    # Load the application icon once and store it globally
    app.setWindowIcon(QIcon("src/assets/icons/icon.svg"))

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the event loop
    sys.exit(app.exec())
