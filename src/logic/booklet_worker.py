# PDFBooklet/src/logic/booklet_worker.py

from PyQt6.QtCore import QObject, pyqtSignal
from .booklet_processor import BookletProcessor


class BookletWorker(QObject):
    """
    A worker object to perform heavy PDF processing (loading or saving)
    on a separate thread.
    """

    processing_finished = pyqtSignal(
        object
    )  # Emits processor (for load) or True (for save)
    processing_failed = pyqtSignal(str)  # Emits error message
    progress_updated = pyqtSignal(int, str)  # Emits percentage and message

    def __init__(
        self,
        pdf_path: str = None,
        processor: BookletProcessor = None,
        output_path: str = None,
        downscale: bool = False,
        target_dpi: int = 300,
        unit: str = "mm",
        output_size=None,
        orientation: str = "portrait",
    ):
        super().__init__()

        # Parameters for Loading (Initial PDF Open)
        self.pdf_path = pdf_path

        # Parameters for Saving (When a processor object already exists)
        self.processor = processor
        self.output_path = output_path
        self.downscale = downscale
        self.target_dpi = target_dpi
        self.unit = unit
        self.output_size = output_size
        self.orientation = orientation  # ADD THIS LINE

    def run(self):
        """
        Loads and processes the PDF document OR saves the booklet.
        This method runs on the worker thread.
        """
        if self.pdf_path and not self.processor:
            self._run_load_pdf()
        elif self.processor and self.output_path:
            self._run_save_booklet()
        else:
            self.processing_failed.emit(
                "Worker initialized with insufficient parameters."
            )

    def _run_load_pdf(self):
        """Logic for initial PDF loading and preview preparation."""
        self.progress_updated.emit(0, "Initializing PDF processor...")
        try:
            # Phase 1: Instantiate the processor and load the PDF
            # Note: BookletProcessor now uses PDFRenderer internally
            processor = BookletProcessor(self.pdf_path)
            self.progress_updated.emit(50, "PDF loaded. Preparing preview data...")

            # Phase 2: Simulate preparation progress
            # Actual rendering happens on-demand in the GUI thread
            total_pages = processor.get_page_count()
            if total_pages > 0:
                for i in range(min(total_pages, 10)):  # Cap at 10 iterations for speed
                    progress_step = 50 + int((i + 1) / min(total_pages, 10) * 50)
                    self.progress_updated.emit(
                        progress_step, f"Preparing preview for booklet page {i+1}..."
                    )

            self.progress_updated.emit(100, "Processing complete.")
            self.processing_finished.emit(processor)

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.processing_failed.emit(f"Error processing PDF: {e}")

    def _run_save_booklet(self):
        """Logic for saving the booklet document using the processor."""
        try:
            # Apply output size from GUI if provided
            if self.output_size is not None:
                self.processor.set_output_size(self.output_size, self.orientation)

            # Delegate to processor's save method
            # The processor will use PDFSaver internally
            success, error_message = self.processor.save_booklet(
                self.output_path,
                self.unit,
                downscale=self.downscale,
                target_dpi=self.target_dpi,
                progress_callback=self.progress_updated.emit,
            )

            if success:
                # Emit True to signify success
                self.processing_finished.emit(True)
            else:
                # Emit the error message
                self.processing_failed.emit(error_message or "Unknown save error")

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.processing_failed.emit(f"Critical error during saving: {e}")
