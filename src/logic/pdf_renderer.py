# PDFBooklet/src/logic/pdf_renderer.py
"""
Pure PDF rendering logic using PyMuPDF (fitz).
Handles ONLY preview generation - no saving, no layout logic.
Supports both stateful (fast, keeps PDF open) and stateless (clean) modes.
"""

import fitz
from PyQt6.QtGui import QPixmap, QImage, QPainter, QTransform
from PyQt6.QtCore import Qt
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .page_transforms import Transform


class PDFRenderer:
    """
    PDF renderer for preview generation.
    Can be used in stateful mode (keeps PDF open) for performance,
    or stateless mode (static methods) for one-off operations.
    """

    def __init__(self, pdf_path: str):
        """
        Initialize renderer with a PDF file.
        Keeps the document open for fast repeated rendering.

        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.page_count = self.doc.page_count

    def close(self):
        """Close the PDF document. Call this when done rendering."""
        if hasattr(self, "doc") and self.doc and not self.doc.is_closed:
            self.doc.close()

    def __del__(self):
        """Ensure document is closed on cleanup."""
        try:
            self.close()
        except:
            pass  # Ignore errors during cleanup

    def render_page(
        self,
        left_idx: int,
        right_idx: int,
        mode: str,
        dpi: int,
        output_width_pt: float,
        output_height_pt: float,
        left_transform: Optional["Transform"] = None,
        right_transform: Optional["Transform"] = None,
    ) -> QPixmap:
        """
        Render a page using the open document (fast).

        Args:
            left_idx: Index of left/top page (-1 for blank)
            right_idx: Index of right/bottom page (-1 for blank)
            mode: 'booklet', 'calendar', or 'single'
            dpi: Resolution for rendering (72/96/150/300/600)
            output_width_pt: Output page width in points
            output_height_pt: Output page height in points
            left_transform: Transform to apply to left/top/single page
            right_transform: Transform to apply to right/bottom page

        Returns:
            QPixmap of the rendered page/spread
        """
        return self._render_internal(
            self.doc,
            left_idx,
            right_idx,
            mode,
            dpi,
            output_width_pt,
            output_height_pt,
            left_transform,
            right_transform,
        )

    @staticmethod
    def render_booklet_page(
        pdf_path: str,
        left_idx: int,
        right_idx: int,
        mode: str,
        dpi: int,
        output_width_pt: float,
        output_height_pt: float,
    ) -> QPixmap:
        """
        Render a single page (stateless - opens and closes PDF).
        Use this for one-off renders. For repeated renders, use instance method.

        Args:
            pdf_path: Path to source PDF
            left_idx: Index of left/top page (-1 for blank)
            right_idx: Index of right/bottom page (-1 for blank)
            mode: 'booklet', 'calendar', or 'single'
            dpi: Resolution for rendering
            output_width_pt: Output page width in points
            output_height_pt: Output page height in points

        Returns:
            QPixmap of the rendered page/spread
        """
        try:
            doc = fitz.open(pdf_path)
            pixmap = PDFRenderer._render_internal(
                doc, left_idx, right_idx, mode, dpi, output_width_pt, output_height_pt
            )
            doc.close()
            return pixmap
        except Exception as e:
            return QPixmap()

    @staticmethod
    def _render_internal(
        doc: fitz.Document,
        left_idx: int,
        right_idx: int,
        mode: str,
        dpi: int,
        output_width_pt: float,
        output_height_pt: float,
        left_transform: Optional["Transform"] = None,
        right_transform: Optional["Transform"] = None,
    ) -> QPixmap:
        """
        Internal rendering logic shared by instance and static methods.
        """
        try:
            # Calculate zoom factor from DPI
            zoom = dpi / 72.0

            # Determine canvas dimensions based on mode
            if mode == "booklet":
                # Side-by-side spread
                canvas_width = int(output_width_pt * zoom * 2)
                canvas_height = int(output_height_pt * zoom)
            elif mode == "calendar":
                # Top-bottom spread
                canvas_width = int(output_width_pt * zoom)
                canvas_height = int(output_height_pt * zoom * 2)
            else:  # single
                canvas_width = int(output_width_pt * zoom)
                canvas_height = int(output_height_pt * zoom)

            # Create blank canvas
            combined_image = QImage(
                canvas_width, canvas_height, QImage.Format.Format_RGB888
            )
            combined_image.fill(Qt.GlobalColor.white)

            painter = QPainter(combined_image)
            mat = fitz.Matrix(zoom, zoom)

            try:
                if mode == "booklet":
                    PDFRenderer._render_booklet_spread(
                        doc,
                        painter,
                        mat,
                        left_idx,
                        right_idx,
                        canvas_width,
                        canvas_height,
                        left_transform,
                        right_transform,
                    )
                elif mode == "calendar":
                    PDFRenderer._render_calendar_spread(
                        doc,
                        painter,
                        mat,
                        left_idx,
                        right_idx,
                        canvas_width,
                        canvas_height,
                        left_transform,
                        right_transform,
                    )
                else:  # single
                    PDFRenderer._render_single_page(
                        doc,
                        painter,
                        mat,
                        left_idx,
                        canvas_width,
                        canvas_height,
                        left_transform,
                    )
            finally:
                painter.end()

            return QPixmap.fromImage(combined_image)
        except Exception as e:
            return QPixmap()

    @staticmethod
    def _render_booklet_spread(
        doc: fitz.Document,
        painter: QPainter,
        matrix: fitz.Matrix,
        left_idx: int,
        right_idx: int,
        canvas_width: int,
        canvas_height: int,
        left_transform: Optional["Transform"] = None,
        right_transform: Optional["Transform"] = None,
    ):
        """Render side-by-side booklet spread with transformations and clipping."""
        page_count = doc.page_count
        half_width = canvas_width // 2
        zoom_factor = matrix.a

        # Render left page
        if 0 <= left_idx < page_count:
            left_pix = doc.load_page(left_idx).get_pixmap(matrix=matrix, alpha=False)
            q_left = QImage(
                left_pix.samples,
                left_pix.width,
                left_pix.height,
                left_pix.stride,
                QImage.Format.Format_RGB888,
            )

            # Scale to fit left half FIRST
            scaled_left = PDFRenderer._scale_image_to_fit(
                q_left, half_width, canvas_height
            )

            # THEN apply transformations (excluding shift)
            if left_transform:
                scaled_left = PDFRenderer._apply_transform_to_image_no_shift(
                    scaled_left, left_transform, zoom_factor
                )

            # Calculate shift offset in pixels
            h_shift_px, v_shift_px = 0, 0
            if left_transform:
                mm_to_px = (72.0 / 25.4) * zoom_factor
                h_shift_px = int(left_transform.h_shift_mm * mm_to_px)
                v_shift_px = -int(left_transform.v_shift_mm * mm_to_px)

            # Center in left half, then apply shift, with clipping
            x_offset = (half_width - scaled_left.width()) // 2 + h_shift_px
            y_offset = (canvas_height - scaled_left.height()) // 2 + v_shift_px

            painter.save()
            painter.setClipRect(0, 0, half_width, canvas_height)
            painter.drawImage(x_offset, y_offset, scaled_left)
            painter.restore()

        # Render right page
        if right_idx != -1 and 0 <= right_idx < page_count:
            right_pix = doc.load_page(right_idx).get_pixmap(matrix=matrix, alpha=False)
            q_right = QImage(
                right_pix.samples,
                right_pix.width,
                right_pix.height,
                right_pix.stride,
                QImage.Format.Format_RGB888,
            )

            # Scale to fit right half FIRST
            scaled_right = PDFRenderer._scale_image_to_fit(
                q_right, half_width, canvas_height
            )

            # THEN apply transformations (excluding shift)
            if right_transform:
                scaled_right = PDFRenderer._apply_transform_to_image_no_shift(
                    scaled_right, right_transform, zoom_factor
                )

            # Calculate shift offset in pixels
            h_shift_px, v_shift_px = 0, 0
            if right_transform:
                mm_to_px = (72.0 / 25.4) * zoom_factor
                h_shift_px = int(right_transform.h_shift_mm * mm_to_px)
                v_shift_px = -int(right_transform.v_shift_mm * mm_to_px)

            # Center in right half, then apply shift, with clipping
            x_offset = (
                half_width + (half_width - scaled_right.width()) // 2 + h_shift_px
            )
            y_offset = (canvas_height - scaled_right.height()) // 2 + v_shift_px

            painter.save()
            painter.setClipRect(half_width, 0, half_width, canvas_height)
            painter.drawImage(x_offset, y_offset, scaled_right)
            painter.restore()

    @staticmethod
    def _render_calendar_spread(
        doc: fitz.Document,
        painter: QPainter,
        matrix: fitz.Matrix,
        top_idx: int,
        bottom_idx: int,
        canvas_width: int,
        canvas_height: int,
        top_transform: Optional["Transform"] = None,
        bottom_transform: Optional["Transform"] = None,
    ):
        """Render top-bottom calendar spread with transformations and clipping."""
        page_count = doc.page_count
        half_height = canvas_height // 2
        zoom_factor = matrix.a

        # Render top page
        if 0 <= top_idx < page_count:
            top_pix = doc.load_page(top_idx).get_pixmap(matrix=matrix, alpha=False)
            q_top = QImage(
                top_pix.samples,
                top_pix.width,
                top_pix.height,
                top_pix.stride,
                QImage.Format.Format_RGB888,
            )

            # Scale to fit top half FIRST
            scaled_top = PDFRenderer._scale_image_to_fit(
                q_top, canvas_width, half_height
            )

            # THEN apply transformations (excluding shift)
            if top_transform:
                scaled_top = PDFRenderer._apply_transform_to_image_no_shift(
                    scaled_top, top_transform, zoom_factor
                )

            # Calculate shift offset in pixels
            h_shift_px, v_shift_px = 0, 0
            if top_transform:
                mm_to_px = (72.0 / 25.4) * zoom_factor
                h_shift_px = int(top_transform.h_shift_mm * mm_to_px)
                v_shift_px = -int(top_transform.v_shift_mm * mm_to_px)

            # Center in top half, then apply shift, with clipping
            x_offset = (canvas_width - scaled_top.width()) // 2 + h_shift_px
            y_offset = (half_height - scaled_top.height()) // 2 + v_shift_px

            painter.save()
            painter.setClipRect(0, 0, canvas_width, half_height)
            painter.drawImage(x_offset, y_offset, scaled_top)
            painter.restore()

        # Render bottom page
        if bottom_idx != -1 and 0 <= bottom_idx < page_count:
            bottom_pix = doc.load_page(bottom_idx).get_pixmap(
                matrix=matrix, alpha=False
            )
            q_bottom = QImage(
                bottom_pix.samples,
                bottom_pix.width,
                bottom_pix.height,
                bottom_pix.stride,
                QImage.Format.Format_RGB888,
            )

            # Scale to fit bottom half FIRST
            scaled_bottom = PDFRenderer._scale_image_to_fit(
                q_bottom, canvas_width, half_height
            )

            # THEN apply transformations (excluding shift)
            if bottom_transform:
                scaled_bottom = PDFRenderer._apply_transform_to_image_no_shift(
                    scaled_bottom, bottom_transform, zoom_factor
                )

            # Calculate shift offset in pixels
            h_shift_px, v_shift_px = 0, 0
            if bottom_transform:
                mm_to_px = (72.0 / 25.4) * zoom_factor
                h_shift_px = int(bottom_transform.h_shift_mm * mm_to_px)
                v_shift_px = -int(bottom_transform.v_shift_mm * mm_to_px)

            # Center in bottom half, then apply shift, with clipping
            x_offset = (canvas_width - scaled_bottom.width()) // 2 + h_shift_px
            y_offset = (
                half_height + (half_height - scaled_bottom.height()) // 2 + v_shift_px
            )

            painter.save()
            painter.setClipRect(0, half_height, canvas_width, half_height)
            painter.drawImage(x_offset, y_offset, scaled_bottom)
            painter.restore()

    @staticmethod
    def _render_single_page(
        doc: fitz.Document,
        painter: QPainter,
        matrix: fitz.Matrix,
        page_idx: int,
        canvas_width: int,
        canvas_height: int,
        page_transform: Optional["Transform"] = None,
    ):
        """Render single page with transformations (no clipping needed)."""
        page_count = doc.page_count
        zoom_factor = matrix.a

        if 0 <= page_idx < page_count:
            page_pix = doc.load_page(page_idx).get_pixmap(matrix=matrix, alpha=False)
            q_page = QImage(
                page_pix.samples,
                page_pix.width,
                page_pix.height,
                page_pix.stride,
                QImage.Format.Format_RGB888,
            )

            # Scale to fit canvas FIRST
            scaled_page = PDFRenderer._scale_image_to_fit(
                q_page, canvas_width, canvas_height
            )

            # THEN apply transformations (excluding shift)
            if page_transform:
                scaled_page = PDFRenderer._apply_transform_to_image_no_shift(
                    scaled_page, page_transform, zoom_factor
                )

            # Calculate shift offset in pixels
            h_shift_px, v_shift_px = 0, 0
            if page_transform:
                mm_to_px = (72.0 / 25.4) * zoom_factor
                h_shift_px = int(page_transform.h_shift_mm * mm_to_px)
                v_shift_px = -int(page_transform.v_shift_mm * mm_to_px)

            # Center on canvas, then apply shift (can go off-canvas)
            x_offset = (canvas_width - scaled_page.width()) // 2 + h_shift_px
            y_offset = (canvas_height - scaled_page.height()) // 2 + v_shift_px
            painter.drawImage(x_offset, y_offset, scaled_page)

    @staticmethod
    def _scale_image_to_fit(image: QImage, max_width: int, max_height: int) -> QImage:
        """
        Scale an image to fit within max dimensions while preserving aspect ratio.
        Scales both up and down as needed.

        Args:
            image: Source image
            max_width: Maximum width
            max_height: Maximum height

        Returns:
            Scaled QImage
        """
        img_width = image.width()
        img_height = image.height()

        # Calculate scale factor to fit within bounds
        scale_w = max_width / img_width
        scale_h = max_height / img_height
        scale = min(scale_w, scale_h)

        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        return image.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    @staticmethod
    def _apply_transform_to_image_no_shift(
        image: QImage, transform: "Transform", zoom_factor: float
    ) -> QImage:
        """
        Apply transformations to an image WITHOUT shift.
        Shift is handled separately as a drawing offset.

        Args:
            image: Source image
            transform: Transform object with all parameters
            zoom_factor: Current DPI zoom factor (dpi/72)

        Returns:
            Transformed QImage
        """
        if not transform:
            return image

        # Check if any transformations need to be applied (excluding shift)
        if (
            transform.rotation_deg == 0
            and not transform.h_flip
            and not transform.v_flip
            and transform.scale_percent == 100.0
            and transform.h_scale_percent == 100.0
            and transform.v_scale_percent == 100.0
        ):
            return image

        # Create transformation matrix
        qt_transform = QTransform()

        # Apply horizontal flip
        if transform.h_flip:
            qt_transform.scale(-1, 1)
            qt_transform.translate(-image.width(), 0)

        # Apply vertical flip
        if transform.v_flip:
            qt_transform.scale(1, -1)
            qt_transform.translate(0, -image.height())

        # Apply rotation around center
        if transform.rotation_deg != 0:
            qt_transform.translate(image.width() / 2, image.height() / 2)
            qt_transform.rotate(transform.rotation_deg)
            qt_transform.translate(-image.width() / 2, -image.height() / 2)

        # Apply non-uniform scaling
        h_scale = (transform.h_scale_percent / 100.0) * (
            transform.scale_percent / 100.0
        )
        v_scale = (transform.v_scale_percent / 100.0) * (
            transform.scale_percent / 100.0
        )

        if h_scale != 1.0 or v_scale != 1.0:
            qt_transform.translate(image.width() / 2, image.height() / 2)
            qt_transform.scale(h_scale, v_scale)
            qt_transform.translate(-image.width() / 2, -image.height() / 2)

        # Apply the transformation
        return image.transformed(
            qt_transform, Qt.TransformationMode.SmoothTransformation
        )

    @staticmethod
    def get_page_size_mm(pdf_path: str) -> Optional[Tuple[float, float]]:
        """
        Get the size of the first page in millimeters.

        Args:
            pdf_path: Path to PDF file

        Returns:
            (width_mm, height_mm) or None on error
        """
        try:
            doc = fitz.open(pdf_path)
            if doc.page_count == 0:
                doc.close()
                return None

            rect = doc[0].rect
            doc.close()

            # Convert points to mm (1 point = 1/72 inch, 1 inch = 25.4mm)
            width_mm = rect.width * 25.4 / 72
            height_mm = rect.height * 25.4 / 72

            return round(width_mm, 2), round(height_mm, 2)
        except Exception as e:
            return None

    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """
        Get the number of pages in a PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages, or 0 on error
        """
        try:
            doc = fitz.open(pdf_path)
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            return 0
