# PDFBooklet/src/main.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# This line ensures that Python finds the modules in the src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set the application's organization and name for QSettings
QApplication.setOrganizationName("PdfBooklet")
QApplication.setApplicationName("PDF Booklet")

from src.gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the application icon once and store it globally
    app.setWindowIcon(QIcon("src/assets/icons/icon.svg"))

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the event loop
    sys.exit(app.exec())
