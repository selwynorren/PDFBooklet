# PDFBooklet/src/gui/about_dialog.py
import os
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QWidget,
    QTextBrowser,
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt


class AboutDialog(QDialog):
    """
    Custom About dialog box.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PDF Booklet")
        self.setFixedSize(320, 320)

        # We are explicitly setting the icon here to ensure it works on all platforms.
        self.setWindowIcon(QIcon("src/assets/icons/icon.svg"))

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        logo = QLabel()
        # Correct path for the logo pixmap from the root directory
        logo.setPixmap(
            QPixmap("src/assets/icons/icon.svg").scaled(
                96,
                96,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(logo)

        # Info
        info = QLabel(
            "<h1><b>PDFBooklet</b></h1>A modern Linux desktop application<br>for creating booklet impositions from PDF files.<br><br>Developer: Selwyn Orren<br>Version: 0.1.0-preview<br><br><a href='https://github.com/selwynorren/pdfbooklet' style='color: #00afff;'>Project on GitHub</a><br><br>"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("font-size: 13px;")
        info.setOpenExternalLinks(True)
        main_layout.addWidget(info)

        # Buttons layout
        button_layout = QHBoxLayout()

        # License button
        license_button = QPushButton("License")
        license_button.clicked.connect(self.show_license)
        button_layout.addWidget(license_button)

        # Spacer to push Close button to the right
        button_layout.addItem(
            QSpacerItem(
                40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
            )
        )

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def _load_license_text(self):
        """Reads the content of the LICENSE file."""
        import sys

        if getattr(sys, "frozen", False):
            # Running as PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

        license_path = os.path.join(base_path, "LICENSE")

        try:
            with open(license_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "LICENSE file not found."
        except Exception as e:
            return f"Error reading LICENSE file: {e}"

    def show_license(self):
        """Displays the license in a new dialog."""
        license_dialog = QDialog(self)
        license_dialog.setWindowTitle("License")
        license_dialog.setFixedSize(500, 400)

        layout = QVBoxLayout()

        license_text_browser = QTextBrowser()
        license_text_browser.setPlainText(self._load_license_text())
        license_text_browser.setStyleSheet("font-size: 14px;")

        layout.addWidget(license_text_browser)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(license_dialog.close)

        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        license_dialog.setLayout(layout)
        license_dialog.exec()
