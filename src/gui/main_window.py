# PDFBooklet/src/gui/main_window.py
import os
import subprocess
import fitz  # PyMuPDF for preview rendering + metadata only
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStatusBar,
    QTabWidget,
    QLabel,
    QFileDialog,
    QProgressBar,
    QFrame,
    QMessageBox,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QSettings, QByteArray, Qt, QThread, QLocale

# Logic imports (PyPDF-based)
from ..logic.booklet_processor import BookletProcessor
from ..logic.booklet_worker import BookletWorker
from ..logic.unit_converter import mm_to_inches

# GUI widgets
from .about_dialog import AboutDialog
from .preview_empty_widget import PreviewEmptyWidget
from .preview_viewer_widget import PreviewViewerWidget
from .control_widget import ControlWidget
from .general_options_widget import GeneralOptionsWidget
from .global_options_widget import GlobalOptionsWidget
from .page_options_widget import PageOptionsWidget
from .advanced_options_widget import AdvancedOptionsWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDF Booklet")

        # PDF state
        self.current_pdf_path = None
        self.booklet_processor = None
        self.current_booklet_page = 0
        self._is_pdf_open = False
        self.current_preview_dpi = 72

        # Page selection state
        self.current_selected_booklet_page = -1
        self.current_selected_side = None

        # Settings
        self.settings = QSettings("PDFBooklet", "PDFBooklet")
        self.load_settings()

        # Threads
        self.processing_thread = None
        self.processing_worker = None
        self.saving_thread = None
        self.saving_worker = None
        self.output_path = None

        # Initialize UI
        self._init_ui()
        self._load_advanced_options_settings()
        self.advanced_options_widget.reset_preview_dpi()
        self.advanced_options_widget.reset_downscale_settings()

        self.advanced_options_widget.locale_changed.connect(self._apply_locale_to_all)

    # ---------------- Settings ----------------
    def load_settings(self):
        if self.settings.contains("window/geometry"):
            self.restoreGeometry(self.settings.value("window/geometry", QByteArray()))
        else:
            self.setGeometry(100, 100, 1200, 800)

    def closeEvent(self, event):
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.save_advanced_options_settings()
        event.accept()

    # ---------------- UI Initialization ----------------
    def _init_ui(self):
        self._create_menu_bar()
        self._create_status_bar()
        self._create_main_layout()

        # Connect signals from all tabs
        for widget in (
            self.general_options_widget,
            self.global_options_widget,
            # self.page_options_widget,
            self.advanced_options_widget,
        ):
            widget.units_changed.connect(self._on_units_changed)
            widget.settings_changed.connect(self._on_advanced_settings_changed)

        # Page options connects to different handler (not advanced settings)
        self.page_options_widget.units_changed.connect(self._on_units_changed)
        self.page_options_widget.settings_changed.connect(
            self._on_page_transform_changed
        )

        # Connect global transformations to trigger preview updates
        self.global_options_widget.h_shift_input.value_changed.connect(
            self._on_global_transform_changed
        )
        self.global_options_widget.v_shift_input.value_changed.connect(
            self._on_global_transform_changed
        )
        self.global_options_widget.scale_input.value_changed.connect(
            self._on_global_transform_changed
        )
        self.global_options_widget.rotation_input.value_changed.connect(
            self._on_global_transform_changed
        )
        self.global_options_widget.h_flip_checkbox.stateChanged.connect(
            self._on_global_transform_changed
        )
        self.global_options_widget.v_flip_checkbox.stateChanged.connect(
            self._on_global_transform_changed
        )
        self.global_options_widget.h_scale_input.value_changed.connect(
            self._on_global_transform_changed
        )
        self.global_options_widget.v_scale_input.value_changed.connect(
            self._on_global_transform_changed
        )

        # Connect page transformations to trigger preview updates
        self.page_options_widget.h_shift_input.value_changed.connect(
            self._on_page_transform_changed
        )
        self.page_options_widget.v_shift_input.value_changed.connect(
            self._on_page_transform_changed
        )
        self.page_options_widget.scale_input.value_changed.connect(
            self._on_page_transform_changed
        )
        self.page_options_widget.rotation_input.value_changed.connect(
            self._on_page_transform_changed
        )
        self.page_options_widget.h_flip_checkbox.stateChanged.connect(
            self._on_page_transform_changed
        )
        self.page_options_widget.v_flip_checkbox.stateChanged.connect(
            self._on_page_transform_changed
        )
        self.page_options_widget.h_scale_input.value_changed.connect(
            self._on_page_transform_changed
        )
        self.page_options_widget.v_scale_input.value_changed.connect(
            self._on_page_transform_changed
        )

        # Connect Preview DPI changes
        self.advanced_options_widget.preview_dpi_combo.currentIndexChanged.connect(
            self._on_preview_dpi_changed
        )

        # Connect domain changes to load appropriate state
        self.page_options_widget.domain_this.toggled.connect(self._on_domain_changed)
        self.page_options_widget.domain_even.toggled.connect(self._on_domain_changed)
        self.page_options_widget.domain_odd.toggled.connect(self._on_domain_changed)

        self._enable_all_tabs(self._is_pdf_open)

        self._update_menu_state()
        self._update_control_widget_state()

    def _enable_all_tabs(self, enabled: bool):
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if widget:
                widget.setEnabled(enabled)

    # ---------------- Menu Bar ----------------
    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("QMenuBar { padding: 5px 5px 5px 6px; }")

        file_menu = menu_bar.addMenu("File")

        self.open_pdf_action = QAction("Open PDF...", self)
        file_menu.addAction(self.open_pdf_action)
        self.open_pdf_action.triggered.connect(self.open_pdf_action_method)

        self.close_pdf_action = QAction("Close PDF", self)
        file_menu.addAction(self.close_pdf_action)
        self.close_pdf_action.triggered.connect(self.close_pdf_action_method)

        file_menu.addSeparator()

        self.save_pdf_action = QAction("Save PDF", self)
        file_menu.addAction(self.save_pdf_action)
        self.save_pdf_action.triggered.connect(self.save_pdf_action_method)

        self.save_as_action = QAction("Save As...", self)
        file_menu.addAction(self.save_as_action)
        self.save_as_action.triggered.connect(self.save_as_action_method)

        file_menu.addSeparator()

        self.quit_action = QAction("Quit", self)
        file_menu.addAction(self.quit_action)
        self.quit_action.triggered.connect(QApplication.instance().quit)

        help_menu = menu_bar.addMenu("Help")

        self.docs_action = QAction("Documentation", self)
        help_menu.addAction(self.docs_action)
        self.docs_action.triggered.connect(self.open_documentation)

        self.about_action = QAction("About", self)
        help_menu.addAction(self.about_action)
        self.about_action.triggered.connect(self.show_about_dialog)

    # ---------------- Status Bar ----------------
    def _create_status_bar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.status_message_label = QLabel("Ready.")
        self.status_message_label.setMinimumWidth(150)
        self.status_message_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_message_label.setStyleSheet("padding: 2px 2px 2px 6px;")
        self.statusBar.addWidget(self.status_message_label)

        self.status_separator = QFrame()
        self.status_separator.setFrameShape(QFrame.Shape.VLine)
        self.status_separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.status_separator.setLineWidth(1)
        self.status_separator.setMidLineWidth(1)
        self.status_separator.setStyleSheet("color: #4040ff;")
        self.status_separator.setVisible(False)
        self.statusBar.addWidget(self.status_separator)

        self.pdf_info_label = QLabel("")
        self.pdf_info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.pdf_info_label.setStyleSheet("padding-left: 10px;")
        self.statusBar.addWidget(self.pdf_info_label, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.statusBar.addPermanentWidget(self.progress_bar)

    # ---------------- Helpers ----------------
    def _cleanup_thread(self, thread_attr: str, worker_attr: str):
        """Generic thread cleanup helper."""
        thread = getattr(self, thread_attr, None)
        if thread and thread.isRunning():
            thread.quit()
            thread.wait()
        setattr(self, thread_attr, None)
        setattr(self, worker_attr, None)

    def _reset_pdf_state(self, message: str = "Ready."):
        """Reset all PDF-related state and UI."""
        self.current_pdf_path = None
        self._is_pdf_open = False
        self.booklet_processor = None
        self.current_booklet_page = 0
        self.current_preview_dpi = 72
        self.advanced_options_widget.reset_preview_dpi()
        self.advanced_options_widget.reset_downscale_settings()
        self._enable_all_tabs(False)
        self.control_widget.setEnabled(False)
        self._update_menu_state()
        self._update_control_widget_state()
        self._update_pdf_info()
        self._update_preview_widget()
        self.status_message_label.setText(message)
        self.status_separator.setVisible(False)

    # ---------------- Main Layout ----------------
    def _create_main_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 0, 10, 0)
        main_layout.setSpacing(0)

        # Left side: tabbed options
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        self.general_options_widget = GeneralOptionsWidget()
        self.global_options_widget = GlobalOptionsWidget()
        self.page_options_widget = PageOptionsWidget()
        self.advanced_options_widget = AdvancedOptionsWidget()

        self.tab_widget.addTab(self.general_options_widget, "General")
        self.tab_widget.addTab(self.global_options_widget, "Global Options")
        self.tab_widget.addTab(self.page_options_widget, "Page Options")
        self.tab_widget.addTab(self.advanced_options_widget, "Advanced")

        left_layout.addWidget(self.tab_widget)

        # Right side: preview + controls
        self.preview_layout = QVBoxLayout()
        self.preview_layout.setContentsMargins(10, 10, 10, 10)
        self.preview_layout.setSpacing(10)

        self.preview_empty_widget = PreviewEmptyWidget()
        self.preview_viewer_widget = None
        self.preview_layout.addWidget(self.preview_empty_widget)

        self.control_widget = ControlWidget()
        self.preview_layout.addWidget(self.control_widget)

        # Connect control signals
        self.control_widget.navigation_widget.first_page_requested.connect(
            self._go_first_page
        )
        self.control_widget.navigation_widget.prev_page_requested.connect(
            self._go_prev_page
        )
        self.control_widget.navigation_widget.next_page_requested.connect(
            self._go_next_page
        )
        self.control_widget.navigation_widget.last_page_requested.connect(
            self._go_last_page
        )

        self.control_widget.update_preview_requested.connect(
            self.update_preview_action_method
        )
        self.control_widget.save_pdf_requested.connect(self.save_pdf_action_method)

        right_widget = QWidget()
        right_widget.setLayout(self.preview_layout)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)

        left_widget.setFixedWidth(367)

    def _on_global_transform_changed(self):
        """Apply global transformations and update preview."""
        if not self.booklet_processor or not self._is_pdf_open:
            return

        transform_dict = self.global_options_widget.get_transformations()
        self.booklet_processor.set_global_transform(transform_dict)
        self._update_preview_widget()

    def _on_page_transform_changed(self):
        """Apply page-specific transformations and update preview."""
        if not self.booklet_processor or not self._is_pdf_open:
            return

        domain = self.page_options_widget.get_domain()

        # Don't do anything if no domain is selected
        if not (
            self.page_options_widget.domain_this.isChecked()
            or self.page_options_widget.domain_even.isChecked()
            or self.page_options_widget.domain_odd.isChecked()
        ):
            return

        transform_dict = self.page_options_widget.get_transformations()

        # Apply transforms directly to the backend (don't save to instance vars yet)
        if domain == "this":
            if self.current_selected_booklet_page < 0 or not self.current_selected_side:
                return

            idx_a, idx_b = self.booklet_processor.get_original_indices_for_booklet_page(
                self.current_selected_booklet_page
            )

            if self.current_selected_side in ["Left", "Top"]:
                if idx_a >= 0:
                    self.booklet_processor.set_page_transform(
                        idx_a, transform_dict, domain
                    )
            elif self.current_selected_side in ["Right", "Bottom"]:
                if idx_b >= 0:
                    self.booklet_processor.set_page_transform(
                        idx_b, transform_dict, domain
                    )
            elif self.current_selected_side == "Whole":
                if idx_a >= 0:
                    self.booklet_processor.set_page_transform(
                        idx_a, transform_dict, domain
                    )

        elif domain == "even":
            self.booklet_processor.set_page_transform(0, transform_dict, "even")

        elif domain == "odd":
            self.booklet_processor.set_page_transform(1, transform_dict, "odd")

        # Update preview
        if self.preview_viewer_widget:
            new_pixmap = self.booklet_processor.render_page(
                self.current_booklet_page, self.current_preview_dpi
            )
            self.preview_viewer_widget._current_pixmap = new_pixmap
            self.preview_viewer_widget._update_pixmap_display()

    # ---------------- Preview Update ----------------
    def _update_preview_widget(self):
        """
        Refreshes the preview widget after processing finishes.
        Regenerates the layout in the booklet_processor based on the selected mode
        and renders the current page.
        """
        if not self.booklet_processor:
            return

        # Safety check: preview viewer must exist
        if not self.preview_viewer_widget:
            return

        # Apply selected output size and orientation from General Options
        selected_output_size = self.general_options_widget.get_output_size()
        selected_orientation = self.general_options_widget.get_orientation()

        self.booklet_processor.set_output_size(
            selected_output_size, selected_orientation
        )

        # Get selected mode from the General Options tab
        selected_mode = self.general_options_widget.get_imposition_mode()

        # ... rest of the method stays the same

        # Regenerate layout in processor
        if selected_mode == "booklet":
            self.booklet_processor.generate_booklet_layout(
                self.booklet_processor.get_original_page_size_mm(),
                (
                    self.booklet_processor.output_width,
                    self.booklet_processor.output_height,
                ),
            )
        elif selected_mode == "calendar":
            self.booklet_processor.generate_calendar_layout(
                self.booklet_processor.get_original_page_size_mm(),
                (
                    self.booklet_processor.output_width,
                    self.booklet_processor.output_height,
                ),
            )
        elif selected_mode == "single":
            self.booklet_processor.generate_single_page_layout(
                self.booklet_processor.get_original_page_size_mm(),
                (
                    self.booklet_processor.output_width,
                    self.booklet_processor.output_height,
                ),
            )

        # Render the current page at current DPI
        # Recreate viewer to pick up new dimensions
        old_viewer = self.preview_viewer_widget
        self.preview_viewer_widget = PreviewViewerWidget(
            processor=self.booklet_processor,
            initial_dpi=self.current_preview_dpi,
            parent=self,
        )
        self.preview_layout.replaceWidget(old_viewer, self.preview_viewer_widget)
        old_viewer.deleteLater()

        # Connect signals
        self.preview_viewer_widget.page_side_selected.connect(
            self._on_page_side_selected
        )

        self.preview_viewer_widget.render_page(
            self.current_booklet_page, self.current_preview_dpi
        )

    # ---------------- PDF Info ----------------
    def _update_pdf_info(self):
        if not self.current_pdf_path or not self.booklet_processor:
            self.pdf_info_label.setText("No PDF loaded.")
            self.status_separator.setVisible(False)
            return
        try:
            title = "Untitled"
            with fitz.open(self.current_pdf_path) as doc:
                meta = doc.metadata
                if meta and meta.get("title"):
                    title = meta["title"]

            original_page_count = self.booklet_processor.original_page_count
            width_mm, height_mm = self.booklet_processor.get_original_page_size_mm()

            current_unit = (
                self.general_options_widget.get_unit()
                or self.advanced_options_widget.get_unit()
            )
            if current_unit == "in":
                width = mm_to_inches(width_mm)
                height = mm_to_inches(height_mm)
                unit_str = "in"
            else:
                width = width_mm
                height = height_mm
                unit_str = "mm"

            info_text = f"Title: {title} | Pages: {original_page_count} | Size: {width:.2f} x {height:.2f} {unit_str}"
            self.pdf_info_label.setText(info_text)
            self.status_separator.setVisible(True)
        except Exception as e:
            self.pdf_info_label.setText("Error loading PDF info.")
            self.status_separator.setVisible(False)

    # ---------------- Menu + Control State ----------------
    def _update_menu_state(self):
        self.close_pdf_action.setEnabled(self._is_pdf_open)
        self.save_pdf_action.setEnabled(self._is_pdf_open)
        self.save_as_action.setEnabled(self._is_pdf_open)

    def _update_control_widget_state(self):
        total_pages = (
            self.booklet_processor.get_page_count() if self.booklet_processor else 0
        )
        self.control_widget.update_state(
            self.current_booklet_page + 1, total_pages, self._is_pdf_open
        )

    # ---------------- Navigation ----------------
    def _go_first_page(self):
        self.current_booklet_page = 0
        self._update_preview_widget()
        self._update_control_widget_state()

    def _go_prev_page(self):
        if self.current_booklet_page > 0:
            self.current_booklet_page -= 1
            self._update_preview_widget()
            self._update_control_widget_state()

    def _go_next_page(self):
        if (
            self.booklet_processor
            and self.current_booklet_page < self.booklet_processor.get_page_count() - 1
        ):
            self.current_booklet_page += 1
            self._update_preview_widget()
            self._update_control_widget_state()

    def _go_last_page(self):
        if self.booklet_processor:
            self.current_booklet_page = self.booklet_processor.get_page_count() - 1
            self._update_preview_widget()
            self._update_control_widget_state()

    # ---------------- PDF Open/Close ----------------
    def open_pdf_action_method(self):
        last_dir = self.settings.value("last_dir", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", last_dir, "PDF Files (*.pdf)"
        )
        if file_path:
            self.settings.setValue("last_dir", os.path.dirname(file_path))
            self.current_pdf_path = file_path
            self.output_path = None  # <-- Reset output path here
            self.start_processing_thread()
        else:
            self.status_message_label.setText("Open cancelled.")

    def close_pdf_action_method(self):
        self._reset_pdf_state("Ready.")
        self.output_path = None  # <-- Reset here too

    # ---------------- Processing Thread ----------------
    def start_processing_thread(self):
        self.status_message_label.setText("Processing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.control_widget.setEnabled(False)
        self.menuBar().setEnabled(False)
        self._enable_all_tabs(False)
        self.status_separator.setVisible(False)

        # Clean up old thread
        self._cleanup_thread("processing_thread", "processing_worker")

        self.processing_thread = QThread()
        self.processing_worker = BookletWorker(pdf_path=self.current_pdf_path)
        self.processing_worker.moveToThread(self.processing_thread)

        self.processing_thread.started.connect(self.processing_worker.run)
        self.processing_worker.progress_updated.connect(self.update_progress_bar)
        self.processing_worker.processing_finished.connect(
            self.processing_finished_handler
        )
        self.processing_worker.processing_failed.connect(self.processing_failed_handler)

        self.processing_worker.processing_finished.connect(self.processing_thread.quit)
        self.processing_worker.processing_failed.connect(self.processing_thread.quit)
        self.processing_thread.finished.connect(self.processing_worker.deleteLater)
        self.processing_thread.finished.connect(self.processing_thread.deleteLater)
        self.processing_thread.finished.connect(
            lambda: setattr(self, "processing_thread", None)
        )
        self.processing_thread.finished.connect(
            lambda: setattr(self, "processing_worker", None)
        )

        self.processing_thread.start()

    # ---------------- Save PDF ----------------
    def save_pdf_action_method(self):
        """Triggered by File > Save PDF or the control widget."""
        if not self.booklet_processor or not self._is_pdf_open:
            QMessageBox.warning(self, "No PDF", "No PDF is currently open.")
            return

        # If we already have an output path, check if file exists and confirm overwrite
        if self.output_path:
            if os.path.exists(self.output_path):
                reply = QMessageBox.question(
                    self,
                    "Overwrite File?",
                    f"The file '{os.path.basename(self.output_path)}' already exists.\nDo you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    self.status_message_label.setText("Save cancelled.")
                    return

            self._perform_save(self.output_path)
        else:
            # No output path yet - use Save As behavior
            self.save_as_action_method()

    def save_as_action_method(self):
        """Triggered by File > Save As..."""
        if not self.current_pdf_path:
            QMessageBox.warning(self, "No PDF", "No PDF is currently open.")
            return

        last_dir = self.settings.value("last_dir", "")

        base_name = os.path.splitext(os.path.basename(self.current_pdf_path))[0]
        suffix = self.advanced_options_widget.get_options().get("suffix", "-bklt")

        suggested_name = f"{base_name}{suffix}.pdf"
        default_path = os.path.join(last_dir, suggested_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF As", default_path, "PDF Files (*.pdf)"
        )

        if file_path:
            self.settings.setValue("last_dir", os.path.dirname(file_path))
            self.output_path = file_path
            self._perform_save(file_path)
        else:
            self.status_message_label.setText("Save cancelled.")

    def _perform_save(self, file_path: str):
        """Perform the actual save using BookletProcessor in a worker thread."""
        self.status_message_label.setText("Saving...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.menuBar().setEnabled(False)
        self.control_widget.setEnabled(False)

        self._cleanup_thread("saving_thread", "saving_worker")

        self.saving_thread = QThread()
        self.saving_worker = BookletWorker(
            pdf_path=self.current_pdf_path,
            output_path=file_path,
            processor=self.booklet_processor,
            downscale=self.advanced_options_widget.get_options().get(
                "downscale", False
            ),
            target_dpi=self.advanced_options_widget.get_options().get(
                "target_dpi", 300
            ),
            unit=self.advanced_options_widget.get_options().get("units", "mm"),
            output_size=self.general_options_widget.get_output_size(),
            orientation=self.general_options_widget.get_orientation(),
        )
        self.saving_worker.moveToThread(self.saving_thread)

        self.saving_thread.started.connect(self.saving_worker.run)
        self.saving_worker.progress_updated.connect(self.update_progress_bar)
        self.saving_worker.processing_finished.connect(self._on_save_finished)
        self.saving_worker.processing_failed.connect(self.processing_failed_handler)

        self.saving_worker.processing_finished.connect(self.saving_thread.quit)
        self.saving_worker.processing_failed.connect(self.saving_thread.quit)
        self.saving_thread.finished.connect(self.saving_worker.deleteLater)
        self.saving_thread.finished.connect(self.saving_thread.deleteLater)
        self.saving_thread.finished.connect(
            lambda: setattr(self, "saving_thread", None)
        )
        self.saving_thread.finished.connect(
            lambda: setattr(self, "saving_worker", None)
        )

        self.saving_thread.start()

    def _on_save_finished(self, result):
        self.progress_bar.setVisible(False)
        self.menuBar().setEnabled(True)
        self.control_widget.setEnabled(True)
        self.status_message_label.setText("Save complete.")

        if self.output_path and os.path.exists(self.output_path):
            try:
                subprocess.Popen(["xdg-open", self.output_path])  # Linux Mint
            except Exception as e:
                QMessageBox.warning(self, "Open PDF", f"Could not open saved PDF: {e}")

    # ---------------- Advanced Settings ----------------
    def _on_units_changed(self, unit: str):
        for widget in (
            self.general_options_widget,
            self.global_options_widget,
            self.page_options_widget,
            self.advanced_options_widget,
        ):
            widget.blockSignals(True)
            widget.update_units(unit)
            widget.blockSignals(False)
        self._update_pdf_info()

    def _on_advanced_settings_changed(self):
        self.save_advanced_options_settings()
        self._update_pdf_info()

    def _on_preview_dpi_changed(self):
        """Update preview DPI and re-render the current page."""
        if not self.booklet_processor or not self._is_pdf_open:
            return

        # Get new DPI from widget
        self.current_preview_dpi = self.advanced_options_widget.get_preview_dpi()

        # Re-render current page at new DPI
        if self.preview_viewer_widget:
            self.preview_viewer_widget.render_page(
                self.current_booklet_page, self.current_preview_dpi
            )

        self.status_message_label.setText(f"Preview DPI: {self.current_preview_dpi}")

    def _load_advanced_options_settings(self):
        settings_data = {
            "units": self.settings.value("advanced_options/units", "mm", type=str),
            "suffix": self.settings.value("advanced_options/suffix", "-bklt", type=str),
            "creep": self.settings.value("advanced_options/creep", 0, type=int),
            "leading_blanks": self.settings.value(
                "advanced_options/leading_blanks", 0, type=int
            ),
            "trailing_blanks": self.settings.value(
                "advanced_options/trailing_blanks", 0, type=int
            ),
            "locale": self.settings.value(
                "advanced_options/locale", "System Default", type=str
            ),
        }
        self.advanced_options_widget.set_options(settings_data)
        self.advanced_options_widget.units_changed.emit(settings_data["units"])
        self._apply_locale_to_all(settings_data["locale"])

    def save_advanced_options_settings(self):
        options = self.advanced_options_widget.get_options()
        for key in options:
            self.settings.setValue(f"advanced_options/{key}", options[key])

    def _apply_locale_to_all(self, locale_string: str):
        if locale_string == "System Default":
            locale = QLocale.system()
        elif locale_string == "English (United States)":
            locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        elif locale_string == "English (United Kingdom)":
            locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom)
        elif locale_string == "English (South Africa)":
            locale = QLocale(QLocale.Language.English, QLocale.Country.SouthAfrica)
        else:
            locale = QLocale.system()

        for tab in (
            self.advanced_options_widget,
            self.global_options_widget,
            self.general_options_widget,
            self.page_options_widget,
        ):
            for child in tab.findChildren(QWidget):
                if hasattr(child, "spinbox"):
                    child.spinbox.setLocale(locale)
                    child.spinbox.setGroupSeparatorShown(False)
                    if child.spinbox.lineEdit():
                        child.spinbox.lineEdit().setLocale(locale)

    # ---------------- Documentation & About ----------------
    def open_documentation(self):
        """Open the user manual PDF from the project root docs folder."""
        try:
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            docs_path = os.path.join(project_root, "docs", "user_manual.pdf")

            if os.path.exists(docs_path):
                subprocess.Popen(["xdg-open", docs_path])
            else:
                QMessageBox.warning(
                    self, "Documentation", f"User manual not found at:\n{docs_path}"
                )
        except Exception as e:
            QMessageBox.warning(
                self, "Documentation", f"Could not open user manual: {e}"
            )

    def show_about_dialog(self):
        """Open the About dialog."""
        try:
            dialog = AboutDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "About", f"Could not open About dialog: {e}")

    # ---------------- Preview Update & Progress ----------------
    def update_preview_action_method(self):
        """Triggered when the control widget requests a preview update."""
        if not self.booklet_processor or not self._is_pdf_open:
            self.status_message_label.setText("No PDF loaded.")
            return

        try:
            self._update_preview_widget()
            self._update_control_widget_state()
            self.status_message_label.setText("Preview updated.")
        except Exception as e:
            self.status_message_label.setText("Error updating preview.")

    def update_progress_bar(self, value: int, message: str = ""):
        """Update the progress bar and status message."""
        if self.progress_bar:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(value)
        if message:
            self.status_message_label.setText(message)

    # ---------------- Processing Handlers ----------------
    def processing_finished_handler(self, processor: BookletProcessor):
        """Called when the worker finishes processing the opened PDF."""
        self.booklet_processor = processor

        # Reset General Options to defaults
        self.general_options_widget.imposition_type_combo.setCurrentIndex(0)  # Booklet
        self.general_options_widget.output_size_combo.setCurrentIndex(0)  # Automatic

        # Reset Global Options transformations to defaults
        self.global_options_widget.h_shift_input.setValue(0)
        self.global_options_widget.v_shift_input.setValue(0)
        self.global_options_widget.scale_input.setValue(100)
        self.global_options_widget.rotation_input.setValue(0)
        self.global_options_widget.h_flip_checkbox.setChecked(False)
        self.global_options_widget.v_flip_checkbox.setChecked(False)
        self.global_options_widget.h_scale_input.setValue(100)
        self.global_options_widget.v_scale_input.setValue(100)

        # Reset Page Options transformations to defaults
        self.page_options_widget.h_shift_input.setValue(0)
        self.page_options_widget.v_shift_input.setValue(0)
        self.page_options_widget.scale_input.setValue(100)
        self.page_options_widget.rotation_input.setValue(0)
        self.page_options_widget.h_flip_checkbox.setChecked(False)
        self.page_options_widget.v_flip_checkbox.setChecked(False)
        self.page_options_widget.h_scale_input.setValue(100)
        self.page_options_widget.v_scale_input.setValue(100)

        # Initialize general options with PDF size
        page_size_mm = self.booklet_processor.get_original_page_size_mm()
        self.general_options_widget.set_original_page_size(page_size_mm)

        # Detect and set orientation based on original page dimensions
        width_mm, height_mm = page_size_mm
        if height_mm > width_mm:
            # Portrait page
            self.general_options_widget.orientation_combo.setCurrentIndex(0)  # Portrait
        else:
            # Landscape page (or square, treat as landscape)
            self.general_options_widget.orientation_combo.setCurrentIndex(
                1
            )  # Landscape

        self._is_pdf_open = True

        # Replace preview widget with fresh viewer for new PDF
        if self.preview_viewer_widget is not None:
            # Remove old viewer
            self.preview_layout.removeWidget(self.preview_viewer_widget)
            self.preview_viewer_widget.deleteLater()
            self.preview_viewer_widget = None
        elif self.preview_empty_widget is not None:
            # Remove empty placeholder (first load only)
            self.preview_layout.removeWidget(self.preview_empty_widget)
            self.preview_empty_widget.deleteLater()
            self.preview_empty_widget = None

        # Create fresh preview viewer
        self.preview_viewer_widget = PreviewViewerWidget(
            processor=self.booklet_processor,
            initial_dpi=self.current_preview_dpi,
            parent=self,
        )
        self.preview_layout.insertWidget(0, self.preview_viewer_widget)

        # Connect signals
        self.preview_viewer_widget.page_side_selected.connect(
            self._on_page_side_selected
        )

        self.progress_bar.setVisible(False)
        self.menuBar().setEnabled(True)
        self.control_widget.setEnabled(True)
        self._enable_all_tabs(True)

        self._update_pdf_info()
        self._update_preview_widget()
        self._update_menu_state()
        self._update_control_widget_state()
        self.status_message_label.setText("PDF loaded successfully.")

    def processing_failed_handler(self, error_message: str):
        """Called if the worker fails to process the PDF."""
        self._reset_pdf_state(f"Processing failed: {error_message}")

    # ---------------- Page Side Selection ----------------
    def _on_page_side_selected(self, booklet_page: int, side: str):
        """Handle when the user clicks a page side in the preview."""
        self.current_selected_booklet_page = booklet_page
        self.current_selected_side = side

        if side is None:
            # Deselected - clear everything
            self.page_options_widget.blockSignals(True)
            self.page_options_widget.domain_this.setAutoExclusive(False)
            self.page_options_widget.domain_even.setAutoExclusive(False)
            self.page_options_widget.domain_odd.setAutoExclusive(False)
            self.page_options_widget.domain_this.setChecked(False)
            self.page_options_widget.domain_even.setChecked(False)
            self.page_options_widget.domain_odd.setChecked(False)
            self.page_options_widget.domain_this.setAutoExclusive(True)
            self.page_options_widget.domain_even.setAutoExclusive(True)
            self.page_options_widget.domain_odd.setAutoExclusive(True)

            self.page_options_widget.set_transformations(
                {
                    "h_shift_mm": 0.0,
                    "v_shift_mm": 0.0,
                    "scale_percent": 100.0,
                    "rotation_deg": 0.0,
                    "h_flip": False,
                    "v_flip": False,
                    "h_scale_percent": 100.0,
                    "v_scale_percent": 100.0,
                }
            )
            self.page_options_widget.blockSignals(False)
            self.status_message_label.setText("No selection")
            return

        # Page selected - load its PER-PAGE-ONLY transforms (not merged with global!)
        idx_a, idx_b = self.booklet_processor.get_original_indices_for_booklet_page(
            booklet_page
        )

        page_idx = -1
        if side in ["Left", "Top", "Whole"]:
            page_idx = idx_a
        elif side in ["Right", "Bottom"]:
            page_idx = idx_b

        if page_idx >= 0:
            # Get the MERGED transform (global + per-page) so user sees current state
            transform = self.booklet_processor.get_transform_for_page(page_idx)

            # Block signals and update UI
            self.page_options_widget.blockSignals(True)

            # Set to "Manually selected page" without triggering signals
            self.page_options_widget.domain_this.blockSignals(True)
            self.page_options_widget.domain_even.blockSignals(True)
            self.page_options_widget.domain_odd.blockSignals(True)
            self.page_options_widget.domain_this.setChecked(True)
            self.page_options_widget.domain_this.blockSignals(False)
            self.page_options_widget.domain_even.blockSignals(False)
            self.page_options_widget.domain_odd.blockSignals(False)

            # Load ONLY the per-page transforms
            transform_dict = {
                "h_shift_mm": transform.h_shift_mm,
                "v_shift_mm": transform.v_shift_mm,
                "scale_percent": transform.scale_percent,
                "rotation_deg": transform.rotation_deg,
                "h_flip": transform.h_flip,
                "v_flip": transform.v_flip,
                "h_scale_percent": transform.h_scale_percent,
                "v_scale_percent": transform.v_scale_percent,
            }
            self.page_options_widget.set_transformations(transform_dict)

            self.page_options_widget.blockSignals(False)

        self.status_message_label.setText(
            f"Selected page {booklet_page + 1}, side: {side}"
        )

    def _on_domain_changed(self):
        """Handle domain selection changes - load appropriate transform state."""
        if not self.booklet_processor or not self._is_pdf_open:
            return

        domain = self.page_options_widget.get_domain()

        # Block signals while updating UI
        self.page_options_widget.blockSignals(True)

        if domain == "this":
            # Manually selected page mode
            if self.current_selected_booklet_page >= 0 and self.current_selected_side:
                (
                    idx_a,
                    idx_b,
                ) = self.booklet_processor.get_original_indices_for_booklet_page(
                    self.current_selected_booklet_page
                )

                page_idx = -1
                if self.current_selected_side in ["Left", "Top", "Whole"]:
                    page_idx = idx_a
                elif self.current_selected_side in ["Right", "Bottom"]:
                    page_idx = idx_b

                if page_idx >= 0:
                    transform = self.booklet_processor.get_transform_for_page(page_idx)
                    transform_dict = {
                        "h_shift_mm": transform.h_shift_mm,
                        "v_shift_mm": transform.v_shift_mm,
                        "scale_percent": transform.scale_percent,
                        "rotation_deg": transform.rotation_deg,
                        "h_flip": transform.h_flip,
                        "v_flip": transform.v_flip,
                        "h_scale_percent": transform.h_scale_percent,
                        "v_scale_percent": transform.v_scale_percent,
                    }
                    self.page_options_widget.set_transformations(transform_dict)
            else:
                self.page_options_widget.set_transformations(
                    {
                        "h_shift_mm": 0.0,
                        "v_shift_mm": 0.0,
                        "scale_percent": 100.0,
                        "rotation_deg": 0.0,
                        "h_flip": False,
                        "v_flip": False,
                        "h_scale_percent": 100.0,
                        "v_scale_percent": 100.0,
                    }
                )

        elif domain == "even":
            # Load from backend
            if self.booklet_processor.transform_manager.even_pages_transform:
                transform = (
                    self.booklet_processor.transform_manager.even_pages_transform
                )
                transform_dict = {
                    "h_shift_mm": transform.h_shift_mm,
                    "v_shift_mm": transform.v_shift_mm,
                    "scale_percent": transform.scale_percent,
                    "rotation_deg": transform.rotation_deg,
                    "h_flip": transform.h_flip,
                    "v_flip": transform.v_flip,
                    "h_scale_percent": transform.h_scale_percent,
                    "v_scale_percent": transform.v_scale_percent,
                }
                self.page_options_widget.set_transformations(transform_dict)
            else:
                self.page_options_widget.set_transformations(
                    {
                        "h_shift_mm": 0.0,
                        "v_shift_mm": 0.0,
                        "scale_percent": 100.0,
                        "rotation_deg": 0.0,
                        "h_flip": False,
                        "v_flip": False,
                        "h_scale_percent": 100.0,
                        "v_scale_percent": 100.0,
                    }
                )

        elif domain == "odd":
            # Load from backend
            if self.booklet_processor.transform_manager.odd_pages_transform:
                transform = self.booklet_processor.transform_manager.odd_pages_transform
                transform_dict = {
                    "h_shift_mm": transform.h_shift_mm,
                    "v_shift_mm": transform.v_shift_mm,
                    "scale_percent": transform.scale_percent,
                    "rotation_deg": transform.rotation_deg,
                    "h_flip": transform.h_flip,
                    "v_flip": transform.v_flip,
                    "h_scale_percent": transform.h_scale_percent,
                    "v_scale_percent": transform.v_scale_percent,
                }
                self.page_options_widget.set_transformations(transform_dict)
            else:
                self.page_options_widget.set_transformations(
                    {
                        "h_shift_mm": 0.0,
                        "v_shift_mm": 0.0,
                        "scale_percent": 100.0,
                        "rotation_deg": 0.0,
                        "h_flip": False,
                        "v_flip": False,
                        "h_scale_percent": 100.0,
                        "v_scale_percent": 100.0,
                    }
                )

        self.page_options_widget.blockSignals(False)
