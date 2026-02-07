# PDFBooklet/src/gui/preview_empty_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt


class PreviewEmptyWidget(QWidget):
    """
    A widget to display the empty state of the preview area.
    Shows a title and instructions.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("PDF Booklet")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        instructions_label = QLabel("Please select your PDF for impositioning.")
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions_label.setStyleSheet("font-size: 14px; color: gray;")
        
        layout.addStretch()
        layout.addWidget(title_label)
        layout.addWidget(instructions_label)
        layout.addStretch()