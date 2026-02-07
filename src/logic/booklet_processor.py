# PDFBooklet/src/logic/booklet_processor.py
"""
Coordinator for PDF booklet processing.
Delegates rendering to PDFRenderer, layout to BookletLayout, and saving to PDFSaver.
Maintains state and coordinates between the three specialized modules.
"""

from typing import Callable, Optional, Tuple
from PyQt6.QtGui import QPixmap

from .booklet_layout import BookletLayout
from .pdf_renderer import PDFRenderer
from .pdf_saver import PDFSaver
from .page_transforms import PageTransformManager, Transform, create_transform_from_gui


class BookletProcessor:
    """
    Thin coordinator that manages PDF booklet state and delegates work.

    Responsibilities:
    - Store PDF path and current settings
    - Manage layout state via BookletLayout
    - Coordinate rendering via PDFRenderer
    - Coordinate saving via PDFSaver
    - Provide convenience methods for the GUI
    """

    def __init__(self, file_path: str):
        """
        Initialize the processor with a PDF file.

        Args:
            file_path: Path to the source PDF
        """
        self.pdf_path = file_path

        # Get page count and original page size
        self.original_page_count = PDFRenderer.get_page_count(file_path)
        page_size = PDFRenderer.get_page_size_mm(file_path)
        self._original_page_size_mm = page_size if page_size else (210.0, 297.0)

        # Initialize layout generator
        self.layout = BookletLayout(self.original_page_count)

        # Initialize transformation manager
        self.transform_manager = PageTransformManager(self.original_page_count)

        # Initialize renderer (keeps PDF open for performance)
        self.renderer = PDFRenderer(file_path)

        # Default to booklet mode
        self.layout.generate_booklet_layout()

        # Default output dimensions (in points) - store SINGLE page dimensions
        # Rendering and saving will adjust based on mode
        original_rect_width = self._original_page_size_mm[0] * 72 / 25.4
        original_rect_height = self._original_page_size_mm[1] * 72 / 25.4
        self.output_width = original_rect_width
        self.output_height = original_rect_height

    @property
    def active_mode(self):
        """Get the current active mode from the layout."""
        return self.layout.active_mode

    def __del__(self):
        """Cleanup renderer on deletion."""
        self.close()

    def close(self):
        """Close the renderer and release resources."""
        if hasattr(self, "renderer") and self.renderer:
            self.renderer.close()

    # ==================== Layout Management ====================

    def generate_booklet_layout(self, original_size, output_size):
        """
        Generate booklet imposition layout.

        Args:
            original_size: Original page size (currently unused, kept for API compatibility)
            output_size: Output page size (currently unused, kept for API compatibility)

        Returns:
            The generated layout map
        """
        return self.layout.generate_booklet_layout()

    def generate_calendar_layout(self, original_size, output_size):
        """
        Generate calendar imposition layout.

        Args:
            original_size: Original page size (currently unused, kept for API compatibility)
            output_size: Output page size (currently unused, kept for API compatibility)

        Returns:
            The generated layout map
        """
        return self.layout.generate_calendar_layout()

    def generate_single_page_layout(self, original_size, output_size):
        """
        Generate single-page layout.

        Args:
            original_size: Original page size (currently unused, kept for API compatibility)
            output_size: Output page size (currently unused, kept for API compatibility)

        Returns:
            The generated layout map
        """
        return self.layout.generate_single_page_layout()

    # ==================== Rendering ====================

    def render_page(self, page_index: int, dpi: int) -> QPixmap:
        """
        Render a page/spread for preview with transformations applied.

        Args:
            page_index: Index in the layout map
            dpi: Resolution for rendering (72/96/150/300/600)

        Returns:
            QPixmap for display
        """
        if page_index < 0 or page_index >= self.layout.get_layout_count():
            return QPixmap()

        # Get page indices from layout
        idx_a, idx_b = self.layout.get_page_indices(page_index)

        # Get transformations for each page
        transform_a = self.get_transform_for_page(idx_a) if idx_a >= 0 else None
        transform_b = self.get_transform_for_page(idx_b) if idx_b >= 0 else None

        # Delegate to renderer with transforms
        return self.renderer.render_page(
            idx_a,
            idx_b,
            self.layout.active_mode,
            dpi,
            self.output_width,  # Single page width
            self.output_height,  # Single page height
            transform_a,
            transform_b,
        )

    # ==================== Saving ====================

    def save_booklet(
        self,
        output_path: str,
        unit: str,
        downscale: bool = False,
        target_dpi: int = 300,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Save the imposed PDF.

        Args:
            output_path: Where to save the output PDF
            unit: Unit system ('mm' or 'in') - currently unused but kept for API compatibility
            downscale: Whether to downsample images
            target_dpi: Target DPI for downsampling
            progress_callback: Optional callback(percent: int, message: str)

        Returns:
            (success: bool, error_message: Optional[str])
        """
        # Calculate output sheet dimensions based on mode
        # output_width/height store SINGLE page dimensions
        if self.layout.active_mode == "booklet":
            # Side-by-side: sheet is 2x wide
            sheet_width = self.output_width * 2
            sheet_height = self.output_height

        elif self.layout.active_mode == "calendar":
            # Top-bottom: sheet is 2x tall
            sheet_width = self.output_width
            sheet_height = self.output_height * 2

        else:  # single
            # One page per sheet
            sheet_width = self.output_width
            sheet_height = self.output_height

        # Delegate to saver
        return PDFSaver.save_booklet(
            source_pdf_path=self.pdf_path,
            output_pdf_path=output_path,
            layout_map=self.layout.active_layout,
            mode=self.layout.active_mode,
            output_width_pt=sheet_width,
            output_height_pt=sheet_height,
            downscale_images=downscale,
            target_dpi=target_dpi,
            progress_callback=progress_callback,
            transform_manager=self.transform_manager,
        )

    # ==================== Accessors ====================

    def get_page_count(self) -> int:
        """Get the number of output pages/spreads."""
        return self.layout.get_layout_count()

    def get_original_indices_for_booklet_page(
        self, booklet_page_index: int
    ) -> Tuple[int, int]:
        """
        Get original PDF page indices for a layout position.

        Args:
            booklet_page_index: Index in the layout map

        Returns:
            (first_page, second_page) tuple, -1 for blank pages
        """
        return self.layout.get_page_indices(booklet_page_index)

    def get_original_page_size_mm(self) -> Tuple[float, float]:
        """
        Get the original PDF page size in millimeters.

        Returns:
            (width_mm, height_mm)
        """
        return self._original_page_size_mm

    def set_output_size(self, output_size, orientation: str = "portrait"):
        """
        Set the output page dimensions.

        Args:
            output_size: Can be:
                - "automatic": Double the original width
                - A preset string: "a4", "a3", "letter", "legal", "tabloid"
                - A tuple: (width, height, unit) where unit is 'mm' or 'in'
        """
        # Get original page dimensions in points
        original_w_mm, original_h_mm = self._original_page_size_mm
        original_w_pt = original_w_mm * 72 / 25.4
        original_h_pt = original_h_mm * 72 / 25.4

        if output_size == "automatic":
            # Use original page dimensions
            self.output_width = original_w_pt
            self.output_height = original_h_pt

            # Apply orientation
            original_is_portrait = (
                self._original_page_size_mm[1] > self._original_page_size_mm[0]
            )
            requested_is_portrait = orientation == "portrait"

            # Swap if requested orientation differs from original
            if original_is_portrait != requested_is_portrait:
                self.output_width, self.output_height = (
                    self.output_height,
                    self.output_width,
                )

        elif isinstance(output_size, str):
            # Preset sizes in mm (always stored as portrait)
            presets_mm = {
                "a4": (210, 297),
                "a3": (297, 420),
                "letter": (216, 279),
                "legal": (216, 356),
                "tabloid": (279, 432),
            }
            if output_size.lower() in presets_mm:
                w_mm, h_mm = presets_mm[output_size.lower()]

                # Apply orientation to preset BEFORE converting to points
                if orientation == "landscape":
                    w_mm, h_mm = h_mm, w_mm  # Swap for landscape

                self.output_width = w_mm * 72 / 25.4
                self.output_height = h_mm * 72 / 25.4
            else:
                # Unknown preset, keep original
                self.output_width = original_w_pt
                self.output_height = original_h_pt

        elif isinstance(output_size, tuple):
            # Custom size: (width, height, unit)
            w, h, unit = output_size

            if unit == "mm":
                self.output_width = w * 72 / 25.4
                self.output_height = h * 72 / 25.4
            elif unit == "in":
                self.output_width = w * 72
                self.output_height = h * 72
            else:
                # Unknown unit, keep original
                self.output_width = original_w_pt
                self.output_height = original_h_pt
        else:
            # Unknown format, keep original
            self.output_width = original_w_pt
            self.output_height = original_h_pt

    # ==================== Transformations ====================

    def set_global_transform(self, transform_dict: dict):
        """
        Set global transformations from GUI values.

        Args:
            transform_dict: Dictionary from global_options_widget.get_transformations()
        """
        transform = create_transform_from_gui(**transform_dict)
        self.transform_manager.set_global_transform(transform)

    def set_page_transform(
        self, page_index: int, transform_dict: dict, domain: str = "this"
    ):
        """
        Set page-specific transformations from GUI values.

        Args:
            page_index: The page index (0-based)
            transform_dict: Dictionary from page_options_widget.get_transformations()
            domain: Domain selector ('this', 'all', 'even', 'odd')
        """
        transform = create_transform_from_gui(**transform_dict)
        self.transform_manager.set_page_transform(page_index, transform, domain)

    def get_transform_for_page(self, page_index: int) -> Transform:
        """
        Get the final merged transformation for a specific page.

        Args:
            page_index: Page index in the original PDF

        Returns:
            Transform object with all merged transformations
        """
        return self.transform_manager.get_transform_for_page(page_index)

    def get_page_only_transform(self, page_index: int) -> Transform:
        """
        Get the per-page-only transform (not merged with global).

        Args:
            page_index: Page index in the original PDF

        Returns:
            Transform object with only the per-page overrides
        """
        return self.transform_manager.get_page_only_transform(page_index)
