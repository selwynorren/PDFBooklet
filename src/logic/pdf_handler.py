# PDFBooklet/src/logic/pdf_handler.py
import PyPDF2


class PDFHandler:
    """Handles all operations related to PDF files."""

    def __init__(self):
        self.reader = None

    def open_pdf(self, file_path):
        """Opens and loads a PDF file."""
        try:
            self.reader = PyPDF2.PdfReader(file_path)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            return False

    def get_page_count(self):
        """Returns the number of pages in the opened PDF."""
        if self.reader:
            return len(self.reader.pages)
        return 0
