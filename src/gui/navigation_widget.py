# PDFBooklet/src/gui/navigation_widget.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal

class NavigationWidget(QWidget):
    """
    A widget that contains all the navigation buttons and the page label.
    """
    # Define signals for button clicks
    first_page_requested = pyqtSignal()
    prev_page_requested = pyqtSignal()
    next_page_requested = pyqtSignal()
    last_page_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        self.first_button = QPushButton("<< First")
        self.prev_button = QPushButton("< Previous")
        self.page_label = QLabel("No PDF loaded")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_button = QPushButton("Next >")
        self.last_button = QPushButton("Last >>")

        for btn in [self.first_button, self.prev_button, self.next_button, self.last_button]:
            btn.setFixedHeight(28)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        main_layout.addWidget(self.first_button)
        main_layout.addWidget(self.prev_button)
        main_layout.addWidget(self.page_label)
        main_layout.addWidget(self.next_button)
        main_layout.addWidget(self.last_button)
        
        # Connect button clicks to signals
        self.first_button.clicked.connect(self.first_page_requested.emit)
        self.prev_button.clicked.connect(self.prev_page_requested.emit)
        self.next_button.clicked.connect(self.next_page_requested.emit)
        self.last_button.clicked.connect(self.last_page_requested.emit)
        
    def update_state(self, current_page: int, total_pages: int, has_pdf: bool):
        """
        Updates the widget's state based on the current PDF.
        """
        if has_pdf:
            self.page_label.setText(f"Page {current_page} of {total_pages}")
            self.first_button.setEnabled(current_page > 1)
            self.prev_button.setEnabled(current_page > 1)
            self.next_button.setEnabled(current_page < total_pages)
            self.last_button.setEnabled(current_page < total_pages)
        else:
            self.page_label.setText("No PDF loaded")
            self.first_button.setEnabled(False)
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.last_button.setEnabled(False)