# PDFBooklet/src/gui/preview_viewer_widget.py

from PyQt6.QtWidgets import QWidget, QLabel, QScrollArea, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QEvent, QPointF, QRectF, pyqtSignal, QObject
from PyQt6.QtGui import (
    QPixmap,
    QResizeEvent,
    QPainter,
    QColor,
    QFont,
    QPen,
    QTextOption,
    QImage,
)
from ..logic.booklet_processor import BookletProcessor


class ClickHandler(QObject):
    """Handles mouse events for the QLabel inside the ScrollArea."""

    clicked = pyqtSignal(QPointF, QPixmap)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                click_pos = event.pos()
                pixmap = watched.pixmap()
                if pixmap and not pixmap.isNull():
                    self.clicked.emit(QPointF(click_pos), pixmap)
                    return True
        return super().eventFilter(watched, event)


class PreviewViewerWidget(QWidget):
    """
    Displays the PDF preview with overlays and selection.
    """

    page_side_selected = pyqtSignal(int, object)

    def __init__(self, processor: BookletProcessor, initial_dpi: int, parent=None):
        super().__init__(parent)
        self.processor = processor
        self.initial_dpi = initial_dpi
        self.current_page_index = 0
        self._current_pixmap = QPixmap()
        self.selected_side = None

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )
        self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)

        self.click_handler = ClickHandler(self)
        self.image_label.installEventFilter(self.click_handler)
        self.click_handler.clicked.connect(self._handle_label_click)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)

        if self.processor:
            self.render_page(0, self.initial_dpi)

    def render_page(self, page_index: int, dpi: int):
        """Render a specific page or spread depending on imposition mode."""
        self.current_page_index = page_index
        self.selected_side = None

        if not self.processor:
            self._current_pixmap = QPixmap()
        else:
            # Always delegate rendering to processor
            self._current_pixmap = self.processor.render_page(page_index, dpi)

        self._update_pixmap_display()
        self.page_side_selected.emit(self.current_page_index, self.selected_side)

    def _handle_label_click(self, click_pos: QPointF, pixmap_with_overlays: QPixmap):
        """Handle click: detect mode, map to region, toggle selection."""
        if not self.processor:
            return

        mode = getattr(self.processor, "active_mode", "booklet")
        label_size = self.image_label.size()
        pixmap_size = pixmap_with_overlays.size()
        offset_x = (label_size.width() - pixmap_size.width()) / 2
        offset_y = (label_size.height() - pixmap_size.height()) / 2
        pixmap_x = click_pos.x() - offset_x
        pixmap_y = click_pos.y() - offset_y

        if (
            pixmap_x < 0
            or pixmap_x > pixmap_size.width()
            or pixmap_y < 0
            or pixmap_y > pixmap_size.height()
        ):
            if self.selected_side is not None:
                self.selected_side = None
                self._update_pixmap_display()
                self.page_side_selected.emit(self.current_page_index, None)
            return

        new_side = None
        if mode == "single":
            new_side = "Whole"
        elif mode == "booklet":
            center_x = pixmap_size.width() / 2
            new_side = "Left" if pixmap_x < center_x else "Right"
        elif mode == "calendar":
            center_y = pixmap_size.height() / 2
            new_side = "Top" if pixmap_y < center_y else "Bottom"

        self.selected_side = None if new_side == self.selected_side else new_side
        self._update_pixmap_display()
        self.page_side_selected.emit(self.current_page_index, self.selected_side)

    def _update_pixmap_display(self):
        """Scale and display current pixmap with overlays and selection."""
        if self._current_pixmap.isNull():
            self.image_label.setText("Error: Could not render page.")
            return

        self.image_label.setText("")
        viewport_size = self.scroll_area.viewport().size()
        if viewport_size.width() <= 0 or viewport_size.height() <= 0:
            return

        scaled_pixmap = self._current_pixmap.scaled(
            viewport_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        overlay_pixmap = QPixmap(scaled_pixmap)
        painter = QPainter(overlay_pixmap)
        try:
            mode = getattr(self.processor, "active_mode", "booklet")

            font = QFont("Georgia", 150, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(255, 0, 0, 128))

            if mode == "single":
                option = QTextOption(Qt.AlignmentFlag.AlignCenter)
                painter.drawText(
                    QRectF(0, 0, overlay_pixmap.width(), overlay_pixmap.height()),
                    str(self._get_single_page_number()),
                    option,
                )
                if self.selected_side == "Whole":
                    painter.setPen(QPen(QColor(255, 0, 0, 255), 3))
                    painter.drawRect(
                        QRectF(0, 0, overlay_pixmap.width(), overlay_pixmap.height())
                    )

            elif mode == "booklet":
                center_x = overlay_pixmap.width() / 2
                pen = QPen(QColor(255, 0, 0, 128), 2, Qt.PenStyle.CustomDashLine)
                pen.setDashPattern([6, 4])
                painter.setPen(pen)
                painter.drawLine(
                    QPointF(center_x, 0), QPointF(center_x, overlay_pixmap.height())
                )
                left_text, right_text = self._get_spread_page_numbers()
                half_width = overlay_pixmap.width() / 2
                option = QTextOption(Qt.AlignmentFlag.AlignCenter)
                painter.drawText(
                    QRectF(0, 0, half_width, overlay_pixmap.height()),
                    str(left_text),
                    option,
                )
                painter.drawText(
                    QRectF(half_width, 0, half_width, overlay_pixmap.height()),
                    str(right_text),
                    option,
                )
                if self.selected_side == "Left":
                    painter.setPen(QPen(QColor(255, 0, 0, 255), 3))
                    painter.drawRect(QRectF(0, 0, half_width, overlay_pixmap.height()))
                elif self.selected_side == "Right":
                    painter.setPen(QPen(QColor(255, 0, 0, 255), 3))
                    painter.drawRect(
                        QRectF(half_width, 0, half_width, overlay_pixmap.height())
                    )

            elif mode == "calendar":
                center_y = overlay_pixmap.height() / 2
                pen = QPen(QColor(255, 0, 0, 128), 2, Qt.PenStyle.CustomDashLine)
                pen.setDashPattern([6, 4])
                painter.setPen(pen)
                painter.drawLine(
                    QPointF(0, center_y), QPointF(overlay_pixmap.width(), center_y)
                )
                top_text, bottom_text = self._get_spread_page_numbers()
                half_height = overlay_pixmap.height() / 2
                option = QTextOption(Qt.AlignmentFlag.AlignCenter)
                painter.drawText(
                    QRectF(0, 0, overlay_pixmap.width(), half_height),
                    str(top_text),
                    option,
                )
                painter.drawText(
                    QRectF(0, half_height, overlay_pixmap.width(), half_height),
                    str(bottom_text),
                    option,
                )
                if self.selected_side == "Top":
                    painter.setPen(QPen(QColor(255, 0, 0, 255), 3))
                    painter.drawRect(QRectF(0, 0, overlay_pixmap.width(), half_height))
                elif self.selected_side == "Bottom":
                    painter.setPen(QPen(QColor(255, 0, 0, 255), 3))
                    painter.drawRect(
                        QRectF(0, half_height, overlay_pixmap.width(), half_height)
                    )
        finally:
            painter.end()

        self.image_label.setPixmap(overlay_pixmap)

    # --- Helpers ---

    def _get_single_page_number(self):
        """Return the original page number for single-page mode."""
        idx_a, _ = self.processor.get_original_indices_for_booklet_page(
            self.current_page_index
        )
        return idx_a + 1 if idx_a != -1 else "?"

    def _get_spread_page_numbers(self):
        """Return left/right or top/bottom page numbers for the current spread."""
        if not self.processor:
            return "?", "?"
        idx_a, idx_b = self.processor.get_original_indices_for_booklet_page(
            self.current_page_index
        )
        text_a = str(idx_a + 1) if idx_a != -1 else ""
        text_b = str(idx_b + 1) if idx_b != -1 else ""
        return text_a, text_b

    # --- Qt events ---

    def showEvent(self, event: QEvent):
        """Called when the widget is shown for the first time."""
        self._update_pixmap_display()
        super().showEvent(event)

    def resizeEvent(self, event: QResizeEvent):
        """Updates the pixmap display when the widget is resized."""
        self._update_pixmap_display()
        super().resizeEvent(event)
