# PDFBooklet/src/logic/pdf_saver.py
"""
PDF saving logic using pypdf for vector-preserving transformations.
Handles all output PDF generation while preserving vector content.
Applies transformations (shift, rotate, scale, flip) during save.
"""

from pypdf import PdfWriter, PdfReader, Transformation, PageObject
from pypdf.generic import RectangleObject
from typing import Callable, Optional, Tuple, TYPE_CHECKING
import math
from pypdf.generic import ArrayObject, NameObject, DictionaryObject
from .image_downscaler import ImageDownscaler

if TYPE_CHECKING:
    from .booklet_layout import LayoutMap
    from .page_transforms import PageTransformManager


class PDFSaver:
    """
    Handles PDF output generation with layout imposition using pypdf.
    Always preserves vector content with full transformation support.
    """

    @staticmethod
    def save_booklet(
        source_pdf_path: str,
        output_pdf_path: str,
        layout_map: "LayoutMap",
        mode: str,
        output_width_pt: float,
        output_height_pt: float,
        downscale_images: bool = False,
        target_dpi: int = 300,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        transform_manager: Optional["PageTransformManager"] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Save an imposed PDF with transformations using pypdf.

        Args:
            source_pdf_path: Path to source PDF
            output_pdf_path: Path to save output PDF
            layout_map: Page arrangement from BookletLayout
            mode: 'booklet', 'calendar', or 'single'
            output_width_pt: Output page width in points
            output_height_pt: Output page height in points
            downscale_images: Whether to downsample raster images
            target_dpi: Target DPI for downsampling (if enabled)
            progress_callback: Optional function(percent: int, message: str)
            transform_manager: Optional PageTransformManager for applying transforms

        Returns:
            (success: bool, error_message: Optional[str])
        """
        try:
            if progress_callback:
                progress_callback(0, "Opening source PDF...")

            # Open source document
            reader = PdfReader(source_pdf_path)
            writer = PdfWriter()

            if progress_callback:
                progress_callback(5, "Preparing output document...")

            total_pages = len(layout_map)

            # Process each page/spread in the layout
            for i, entry in enumerate(layout_map):
                # Determine page indices
                if isinstance(entry, tuple):
                    idx_a, idx_b = entry
                else:
                    idx_a, idx_b = entry, -1

                # Create new output page with correct dimensions
                output_page = PageObject.create_blank_page(
                    width=output_width_pt, height=output_height_pt
                )

                # Place pages according to mode
                if mode == "booklet":
                    # Get transforms for this spread
                    left_transform = (
                        transform_manager.get_transform_for_page(idx_a)
                        if (transform_manager and idx_a >= 0)
                        else None
                    )
                    right_transform = (
                        transform_manager.get_transform_for_page(idx_b)
                        if (transform_manager and idx_b >= 0)
                        else None
                    )

                    PDFSaver._place_booklet_spread(
                        reader,
                        output_page,
                        idx_a,
                        idx_b,
                        output_width_pt,
                        output_height_pt,
                        left_transform,
                        right_transform,
                    )
                elif mode == "calendar":
                    # Get transforms for this spread
                    top_transform = (
                        transform_manager.get_transform_for_page(idx_a)
                        if (transform_manager and idx_a >= 0)
                        else None
                    )
                    bottom_transform = (
                        transform_manager.get_transform_for_page(idx_b)
                        if (transform_manager and idx_b >= 0)
                        else None
                    )

                    PDFSaver._place_calendar_spread(
                        reader,
                        output_page,
                        idx_a,
                        idx_b,
                        output_width_pt,
                        output_height_pt,
                        top_transform,
                        bottom_transform,
                    )
                else:  # single
                    # Get transform for this page
                    page_transform = (
                        transform_manager.get_transform_for_page(idx_a)
                        if (transform_manager and idx_a >= 0)
                        else None
                    )

                    PDFSaver._place_single_page(
                        reader,
                        output_page,
                        idx_a,
                        output_width_pt,
                        output_height_pt,
                        page_transform,
                    )

                # Add the completed page to output
                # Ensure page size is preserved
                output_page.mediabox.lower_left = (0, 0)
                output_page.mediabox.upper_right = (output_width_pt, output_height_pt)
                writer.add_page(output_page)

                # Update progress
                if progress_callback:
                    percent = int(5 + ((i + 1) / total_pages) * 90)
                    progress_callback(
                        percent, f"Assembling page {i + 1} of {total_pages}..."
                    )

            # Downsample images if requested
            if downscale_images:
                if progress_callback:
                    progress_callback(92, "Downsampling images...")

                ImageDownscaler.downsample_images_in_writer(
                    writer,
                    target_dpi=target_dpi,
                    progress_callback=None,  # Avoid nested progress updates
                )

            if progress_callback:
                progress_callback(95, "Writing PDF to disk...")

            # Write output PDF
            with open(output_pdf_path, "wb") as output_file:
                writer.write(output_file)

            if progress_callback:
                progress_callback(100, "Save complete!")

            return True, None

        except Exception as e:
            import traceback

            error_msg = f"Save failed: {str(e)}"
            traceback.print_exc()
            if progress_callback:
                progress_callback(0, error_msg)
            return False, error_msg

    @staticmethod
    def _place_booklet_spread(
        reader: PdfReader,
        output_page: PageObject,
        left_idx: int,
        right_idx: int,
        width_pt: float,
        height_pt: float,
        left_transform=None,
        right_transform=None,
    ):
        """Place pages side-by-side for booklet mode with transformations."""
        half_width = width_pt / 2

        # Place left page
        if 0 <= left_idx < len(reader.pages):
            target_rect = (0, 0, half_width, height_pt)
            PDFSaver._merge_page_with_transform(
                reader, output_page, left_idx, target_rect, left_transform
            )

        # Place right page
        if right_idx != -1 and 0 <= right_idx < len(reader.pages):
            target_rect = (half_width, 0, width_pt, height_pt)
            PDFSaver._merge_page_with_transform(
                reader, output_page, right_idx, target_rect, right_transform
            )

    @staticmethod
    def _place_calendar_spread(
        reader: PdfReader,
        output_page: PageObject,
        top_idx: int,
        bottom_idx: int,
        width_pt: float,
        height_pt: float,
        top_transform=None,
        bottom_transform=None,
    ):
        """Place pages top-bottom for calendar mode with transformations."""
        half_height = height_pt / 2

        # Place top page (upper half in visual terms, which is higher Y in PDF coords)
        if 0 <= top_idx < len(reader.pages):
            target_rect = (0, half_height, width_pt, height_pt)
            PDFSaver._merge_page_with_transform(
                reader, output_page, top_idx, target_rect, top_transform
            )

        # Place bottom page (lower half in visual terms, which is lower Y in PDF coords)
        if bottom_idx != -1 and 0 <= bottom_idx < len(reader.pages):
            target_rect = (0, 0, width_pt, half_height)
            PDFSaver._merge_page_with_transform(
                reader, output_page, bottom_idx, target_rect, bottom_transform
            )

    @staticmethod
    def _place_single_page(
        reader: PdfReader,
        output_page: PageObject,
        page_idx: int,
        width_pt: float,
        height_pt: float,
        page_transform=None,
    ):
        """Place single page full-size with transformations."""
        if 0 <= page_idx < len(reader.pages):
            target_rect = (0, 0, width_pt, height_pt)
            PDFSaver._merge_page_with_transform(
                reader, output_page, page_idx, target_rect, page_transform
            )

    @staticmethod
    def _merge_page_with_transform(
        reader: PdfReader,
        output_page: PageObject,
        source_idx: int,
        target_rect: tuple,  # (x0, y0, x1, y1)
        transform=None,
    ):
        """
        Merge a source page onto output page with transformations and clipping using Form XObjects.

        Args:
            reader: Source PDF reader
            output_page: Destination page object
            source_idx: Index of source page
            target_rect: Target rectangle (x0, y0, x1, y1) in points
            transform: Optional Transform object
        """
        from pypdf.generic import (
            DecodedStreamObject,
            DictionaryObject,
            ArrayObject,
            FloatObject,
            RectangleObject,
        )

        source_page = reader.pages[source_idx]

        # Get source page dimensions
        src_box = source_page.mediabox
        src_width = float(src_box.width)
        src_height = float(src_box.height)

        # Target rectangle dimensions
        x0, y0, x1, y1 = target_rect
        target_width = x1 - x0
        target_height = y1 - y0

        # Calculate base scaling to fit target rectangle
        scale_x = target_width / src_width
        scale_y = target_height / src_height
        base_scale = min(scale_x, scale_y)

        # Calculate initial fitted dimensions (before user transforms)
        fitted_width = src_width * base_scale
        fitted_height = src_height * base_scale

        # Build transformation
        if transform and not transform.is_identity():
            # User scale factors
            h_scale = (transform.h_scale_percent / 100.0) * (
                transform.scale_percent / 100.0
            )
            v_scale = (transform.v_scale_percent / 100.0) * (
                transform.scale_percent / 100.0
            )

            # Final scaled dimensions (before rotation)
            final_width = fitted_width * abs(h_scale)
            final_height = fitted_height * abs(v_scale)

            # Center position based on scaled (but not rotated) dimensions
            center_x = x0 + (target_width - final_width) / 2
            center_y = y0 + (target_height - final_height) / 2

            # Calculate final scaling including user transforms
            final_scale_x = base_scale * h_scale
            final_scale_y = base_scale * v_scale

            # Handle flips
            is_h_flipped = transform.h_flip
            is_v_flipped = transform.v_flip

            if is_h_flipped:
                final_scale_x = -final_scale_x
            if is_v_flipped:
                final_scale_y = -final_scale_y

            # Adjust rotation angle if flipped
            rotation_deg = transform.rotation_deg
            if is_h_flipped:
                rotation_deg = -rotation_deg
            if is_v_flipped:
                rotation_deg = -rotation_deg

            # Convert shift from mm to points
            shift_x_pt = transform.h_shift_mm * 72 / 25.4
            shift_y_pt = transform.v_shift_mm * 72 / 25.4

            # Source center point
            src_center_x = src_width / 2
            src_center_y = src_height / 2

            # Build transformation matrix
            transformation = (
                Transformation()
                .translate(tx=-src_center_x, ty=-src_center_y)
                .scale(sx=final_scale_x, sy=final_scale_y)
            )

            if rotation_deg != 0:
                transformation = transformation.rotate(-rotation_deg)

            # Final position: need to account for source center
            final_x = center_x + src_center_x * base_scale * abs(h_scale) + shift_x_pt
            final_y = center_y + src_center_y * base_scale * abs(v_scale) + shift_y_pt

            transformation = transformation.translate(tx=final_x, ty=final_y)
        else:
            # No transform - simple scale and center
            center_x = x0 + (target_width - fitted_width) / 2
            center_y = y0 + (target_height - fitted_height) / 2

            # When scale is 1.0 (content fits exactly), just translate to target origin
            if abs(base_scale - 1.0) < 0.001:
                transformation = Transformation().translate(tx=x0, ty=y0)
            else:
                # Need to match the transform path logic
                src_center_x = src_width / 2
                src_center_y = src_height / 2

                transformation = (
                    Transformation()
                    .translate(tx=-src_center_x, ty=-src_center_y)
                    .scale(sx=base_scale, sy=base_scale)
                    .translate(
                        tx=center_x + fitted_width / 2, ty=center_y + fitted_height / 2
                    )
                )

        # Get transformation matrix
        ctm = transformation.ctm

        # Clean up floating-point errors in the CTM
        # Values very close to 0, 1, or -1 should be exact for better PDF compatibility
        cleaned_ctm = []
        for value in ctm:
            if abs(value) < 1e-10:  # Essentially zero
                cleaned_ctm.append(0.0)
            elif abs(value - 1.0) < 1e-10:  # Essentially 1
                cleaned_ctm.append(1.0)
            elif abs(value + 1.0) < 1e-10:  # Essentially -1
                cleaned_ctm.append(-1.0)
            else:
                cleaned_ctm.append(value)

        ctm = tuple(cleaned_ctm)

        # Create a Form XObject from the source page
        # This encapsulates the page content and resources in an isolated object
        form_xobject = DictionaryObject()
        form_xobject[NameObject("/Type")] = NameObject("/XObject")
        form_xobject[NameObject("/Subtype")] = NameObject("/Form")
        form_xobject[NameObject("/FormType")] = FloatObject(1)

        # Set the BBox to match source page dimensions
        form_xobject[NameObject("/BBox")] = ArrayObject(
            [
                FloatObject(0),
                FloatObject(0),
                FloatObject(src_width),
                FloatObject(src_height),
            ]
        )

        # Copy the source page's content stream to the Form XObject
        source_content = source_page.get_contents()
        if source_content is None:
            return  # Nothing to merge

        source_data = source_content.get_data()

        # Create a Form XObject from the source page
        from pypdf.generic import StreamObject

        # Create stream object for the Form XObject
        form_stream = StreamObject()
        form_stream._data = source_data

        # Set Form XObject properties
        form_stream[NameObject("/Type")] = NameObject("/XObject")
        form_stream[NameObject("/Subtype")] = NameObject("/Form")
        form_stream[NameObject("/FormType")] = FloatObject(1)

        # Set the BBox to match source page dimensions
        form_stream[NameObject("/BBox")] = ArrayObject(
            [
                FloatObject(0),
                FloatObject(0),
                FloatObject(src_width),
                FloatObject(src_height),
            ]
        )

        # Copy the source page's resources to the Form XObject
        if "/Resources" in source_page:
            form_stream[NameObject("/Resources")] = source_page["/Resources"]

        form_xobject = form_stream
        # Copy the source page's resources to the Form XObject
        # This isolates resources - no conflicts with output page resources
        if "/Resources" in source_page:
            form_xobject[NameObject("/Resources")] = source_page["/Resources"]

        # Add the Form XObject to output page's resources
        if "/Resources" not in output_page:
            output_page[NameObject("/Resources")] = DictionaryObject()

        if "/XObject" not in output_page["/Resources"]:
            output_page["/Resources"][NameObject("/XObject")] = DictionaryObject()

        # Generate unique name for this Form XObject
        xobj_name = f"/Fm{source_idx}"
        output_page["/Resources"]["/XObject"][NameObject(xobj_name)] = form_xobject

        # Build content stream that references the Form XObject
        # This applies clipping and transformation, then invokes the Form XObject
        new_content = f"""q
    {x0} {y0} {target_width} {target_height} re
    W
    n
    q
    {ctm[0]} {ctm[1]} {ctm[2]} {ctm[3]} {ctm[4]} {ctm[5]} cm
    {xobj_name} Do
    Q
    Q
    """.encode()

        # Get existing content from output page
        existing_content = output_page.get_contents()

        if existing_content is not None:
            # Append to existing content
            existing_data = existing_content.get_data()
            combined_content = existing_data + b"\n" + new_content
        else:
            combined_content = new_content

        # Create new content stream and replace
        content_stream = DecodedStreamObject()
        content_stream.set_data(combined_content)

        # Set the combined content
        output_page[NameObject("/Contents")] = content_stream
