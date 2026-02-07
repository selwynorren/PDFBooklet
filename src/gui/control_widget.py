# PDFBooklet/src/gui/control_widget.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from .navigation_widget import NavigationWidget

class ControlWidget(QWidget):
    """
    A widget that contains all the navigation and control buttons.
    """
    # Define signals for button clicks
    update_preview_requested = pyqtSignal()
    save_pdf_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Navigation widget will be on the left
        self.navigation_widget = NavigationWidget()

        # Spacer to push the navigation to the left
        main_layout.addStretch()

        # Add the navigation widget
        main_layout.addWidget(self.navigation_widget, 0, Qt.AlignmentFlag.AlignLeft)

        # Add a flexible spacer to push the other buttons to the right
        main_layout.addStretch(1)

        # Update Preview button
        self.update_button = QPushButton("Update Preview")
        self.update_button.setFixedHeight(28)
        self.update_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Apply a darker blue color palette for better contrast
        palette = self.update_button.palette()
        palette.setColor(QPalette.ColorRole.Button, QColor(0, 51, 153))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        self.update_button.setPalette(palette)
        self.update_button.setAutoFillBackground(True)

        # Save PDF button
        self.save_button = QPushButton("Save PDF")
        self.save_button.setFixedHeight(28)
        self.save_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Apply a darker red color palette for better contrast
        palette = self.save_button.palette()
        palette.setColor(QPalette.ColorRole.Button, QColor(153, 0, 0))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        self.save_button.setPalette(palette)
        self.save_button.setAutoFillBackground(True)

        # Add the update and save buttons
        main_layout.addWidget(self.update_button)
        main_layout.addWidget(self.save_button)

        # Connect button clicks to signals
        self.update_button.clicked.connect(self.update_preview_requested.emit)
        self.save_button.clicked.connect(self.save_pdf_requested.emit)
        
    def update_state(self, current_page: int, total_pages: int, has_pdf: bool):
        """
        Updates the child widgets' state.
        """
        self.update_button.setEnabled(has_pdf)
        self.save_button.setEnabled(has_pdf)
        self.navigation_widget.update_state(current_page, total_pages, has_pdf)