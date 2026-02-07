# PDFBooklet/src/logic/image_downscaler.py
"""
Image downscaling utilities for PDF optimization.
Downsamples raster images in PDFs to reduce file size while preserving vectors.
"""

from PIL import Image
import io
from pypdf import PdfWriter
from pypdf.generic import NameObject, DictionaryObject, NumberObject
from typing import Optional


class ImageDownscaler:
    """Handles downsampling of raster images in PDFs."""

    @staticmethod
    def downsample_images_in_writer(
        writer: PdfWriter,
        target_dpi: int = 300,
        progress_callback: Optional[callable] = None,
    ):
        """
        Downsample all images in a PdfWriter to target DPI.

        Args:
            writer: PdfWriter object with pages to process
            target_dpi: Target DPI for images (default 300)
            progress_callback: Optional callback(percent, message)
        """
        total_pages = len(writer.pages)

        for page_num, page in enumerate(writer.pages):
            if progress_callback:
                percent = int((page_num / total_pages) * 100)
                progress_callback(
                    percent, f"Downsampling images on page {page_num + 1}..."
                )

            # Process images on this page
            ImageDownscaler._process_page_images(page, target_dpi)

        if progress_callback:
            progress_callback(100, "Image downsampling complete")

    @staticmethod
    def _process_page_images(page, target_dpi: int):
        """Process all images on a single page."""
        # Check if page has resources
        if "/Resources" not in page:
            return

        # Process images recursively (including those inside Form XObjects)
        ImageDownscaler._process_resources(page["/Resources"], target_dpi)

    @staticmethod
    def _process_resources(resources, target_dpi: int):
        """Recursively process resources to find and downsample images."""
        if not resources or "/XObject" not in resources:
            return

        xobjects = resources["/XObject"].get_object()

        for obj_name in list(xobjects.keys()):
            obj = xobjects[obj_name]

            if isinstance(obj, dict) or hasattr(obj, "get_object"):
                obj = obj.get_object() if hasattr(obj, "get_object") else obj

                subtype = obj.get("/Subtype") or obj.get(NameObject("/Subtype"))

                if subtype == "/Image" or subtype == NameObject("/Image"):
                    # This is an actual image
                    ImageDownscaler._downsample_image(
                        xobjects, obj_name, obj, target_dpi
                    )

                elif subtype == "/Form" or subtype == NameObject("/Form"):
                    # This is a Form XObject - check inside it for images
                    if "/Resources" in obj:
                        ImageDownscaler._process_resources(
                            obj["/Resources"], target_dpi
                        )

    @staticmethod
    def _downsample_image(xobjects_dict, obj_name, image_obj, target_dpi: int):
        """
        Downsample a single image if it exceeds target DPI.
        Returns True if image was downsampled, False otherwise.
        """
        try:
            # Get image dimensions
            width = image_obj.get("/Width")
            height = image_obj.get("/Height")

            if not width or not height:
                return False

            # Get image data
            data = image_obj.get_data()
            if not data:
                return False

            # Determine image format
            filter_type = image_obj.get("/Filter")

            # Convert to PIL Image
            try:
                # Handle different filter types
                if filter_type == "/DCTDecode" or filter_type == NameObject(
                    "/DCTDecode"
                ):
                    # JPEG - can load directly
                    pil_image = Image.open(io.BytesIO(data))
                elif filter_type == "/FlateDecode" or filter_type == NameObject(
                    "/FlateDecode"
                ):
                    # FlateDecode images have decoding/inversion issues - skip them
                    return False
                else:
                    # Unsupported filter - skip
                    return False

            except Exception:
                # Can't decode image - skip
                return False

            # Calculate target dimensions
            max_print_size_inches = 11
            target_pixels = int(max_print_size_inches * target_dpi)

            # Check if downsampling is needed
            needs_downsample = max(width, height) > target_pixels

            if not needs_downsample:
                return False

            # Calculate new dimensions maintaining aspect ratio
            aspect_ratio = width / height
            if width > height:
                new_width = target_pixels
                new_height = max(1, int(target_pixels / aspect_ratio))
            else:
                new_height = target_pixels
                new_width = max(1, int(target_pixels * aspect_ratio))

            # Safety check: ensure both dimensions are at least 1
            new_width = max(1, new_width)
            new_height = max(1, new_height)

            # Downsample the image
            downsampled = pil_image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )

            # Re-encode as JPEG (only DCTDecode images reach here)
            output_buffer = io.BytesIO()
            if downsampled.mode != "RGB":
                downsampled = downsampled.convert("RGB")
            downsampled.save(output_buffer, format="JPEG", quality=85, optimize=True)
            new_filter = NameObject("/DCTDecode")

            new_data = output_buffer.getvalue()

            # Create new stream object
            from pypdf.generic import DecodedStreamObject

            new_stream = DecodedStreamObject()
            new_stream.set_data(new_data)
            new_stream[NameObject("/Type")] = NameObject("/XObject")
            new_stream[NameObject("/Subtype")] = NameObject("/Image")
            new_stream[NameObject("/Width")] = NumberObject(new_width)
            new_stream[NameObject("/Height")] = NumberObject(new_height)
            new_stream[NameObject("/Filter")] = new_filter
            new_stream[NameObject("/ColorSpace")] = NameObject("/DeviceRGB")
            new_stream[NameObject("/BitsPerComponent")] = NumberObject(8)

            # Replace in XObjects dictionary
            xobjects_dict[obj_name] = new_stream

            return True

        except Exception:
            # If anything fails, skip this image
            return False
