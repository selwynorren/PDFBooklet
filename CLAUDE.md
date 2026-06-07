# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A PyQt6 Linux desktop app that creates booklet impositions (and calendar/single-page layouts) from PDF files, with per-page transforms, image downsampling, and a live preview.

## Commands

```bash
source .venv/bin/activate            # venv lives in repo root (Python 3.10)
pip install -r requirements.txt      # runtime: PyQt6, pypdf, Pillow, PyMuPDF
pip install -r requirements-dev.txt  # adds pytest
python main.py                       # run the app
pytest                               # run the full test suite
```

Tests (`tests/`, run headless via `conftest.py` setting `QT_QPA_PLATFORM=offscreen`) cover: layout (`test_imposition`), transform compounding (`test_page_transforms`), output-size semantics (`test_output_size`), the `SettingsStore` (`test_settings_store`), combo userData keys (`test_general_options`), golden save structure + save centering (`test_save_golden`, `test_save_centering`), image downscaling (`test_downscaler`), and end-to-end processor save (`test_processor_e2e`). The on-screen **preview** compositing (`pdf_renderer.py`) is still not under test.

Build the distributable AppImage with the full PyInstaller + appimagetool sequence in the `Build & Packaging Instructions` file (it bundles `LICENSE`, `docs/`, and `src/assets/` into a one-file executable, then wraps it in an AppDir). `PDFBooklet.spec` is the generated PyInstaller spec.

Note: `.gitignore` excludes `build/`, `dist/`, `*.spec`, `*.AppImage`, and `Build & Packaging Instructions` — packaging artifacts are not tracked.

## Architecture

Entry point is the top-level `main.py`, which fixes `sys.path`, sets `QApplication` org/name, installs the `QTranslator` (see Translations below), and launches `src/gui/main_window.py`.

The codebase splits into **three tiers with a one-way dependency rule** (GUI → Logic → Data; lower tiers never import upward):
- **Data** (`src/data/`) — persistence and plain data models. Imports nothing from logic/gui.
- **Logic** (`src/logic/`) — PDF render/save/layout/transforms. No GUI widgets. (Uses Qt only where noted: the preview renderer and the threading worker.)
- **GUI** (`src/gui/`) — widgets only; no PDF math, no direct settings keys.

### Two PDF libraries, two jobs

This is the most important thing to understand before touching PDF code:

- **PyMuPDF (`fitz`)** — used **only** for fast preview rendering and metadata/page-size reads (`pdf_renderer.py`, plus `main_window.py`). The renderer keeps the document open (stateful mode) for repeated fast rendering. `pdf_renderer.py` also uses Qt's raster engine (QImage/QPainter/QTransform/QPixmap) to composite the preview — this is **by design** (drawing pixels for the screen is a display job) and is a documented exception to "logic is Qt-free", in the same category as the QObject worker. Do not rewrite it for purity; the preview path is untested and divergence-prone.
- **pypdf** — used **only** for saving output (`pdf_saver.py`). Saves are **vector-preserving**; transforms (shift/rotate/scale/flip) are applied as pypdf `Transformation` matrices at save time, not rasterized.

All PDF work goes through `pdf_renderer` (preview) and `pdf_saver` (output). The old `PyPDF2`-based `pdf_handler.py` has been removed — do not reintroduce PyPDF2 (it is deprecated; `pypdf` is its successor).

### Data layer (`src/data/`)

- **`models.py`** — plain data models, no Qt/PDF (currently the `Transform` dataclass; measurements in **mm**, scale in **percent**, rotation in **degrees**).
- **`settings_store.py`** — `SettingsStore` wraps `QSettings("PDFBooklet", "PDFBooklet")` behind typed accessors (window geometry, last dir, advanced options). The GUI goes through this; it never touches storage keys directly. (QSettings is Qt, but persistence is a data concern, so it lives here.)

### Logic layer (`src/logic/`)

- **`booklet_processor.py`** — the coordinator. Holds state (PDF path, page count, original page size) and delegates: layout to `BookletLayout`, preview to `PDFRenderer`, saving to `PDFSaver`, transforms to `PageTransformManager`. The GUI talks mostly to this class.
- **`booklet_layout.py`** — pure layout generation. Produces a `LayoutMap` (list of page-index pairs/singles) for booklet/calendar/single modes. No I/O, no rendering. Handles booklet padding (pads to a multiple of 4).
- **`page_transforms.py`** — `PageTransformManager`, whose `get_transform_for_page()` compounds three layers (global + even/odd domain + per-page override) into the final `Transform`. `create_transform_from_gui()` bridges GUI widget values into a `Transform`. (The `Transform` model itself now lives in `src/data/models.py`; `page_transforms` re-exports it for back-compat.)
- **`pdf_renderer.py` / `pdf_saver.py`** — rendering and saving as described above.
- **`image_downscaler.py`** — optional image downsampling applied during save to shrink output file size (target DPI based).
- **`booklet_worker.py`** — a `QObject` worker run on a `QThread` for the two heavy operations: **loading** a PDF (constructs a `BookletProcessor`) and **saving** a booklet. Mode is chosen by which constructor args are set (`pdf_path` alone → load; `processor` + `output_path` → save). Communicates via `processing_finished` / `processing_failed` / `progress_updated` signals.
- **`unit_converter.py`** — mm/inch conversion helpers (the app supports both unit systems and locale switching).

### GUI layer (`src/gui/`)

`main_window.py` (`MainWindow`) is the orchestrator: it owns the `BookletProcessor`, manages the load/save `QThread`s, persists UI state via `SettingsStore` (the data tier), and assembles the tabbed options panels — `GeneralOptionsWidget`, `GlobalOptionsWidget`, `PageOptionsWidget`, `AdvancedOptionsWidget` — alongside the preview (`PreviewViewerWidget` / `PreviewEmptyWidget`) and `ControlWidget`. Locale changes propagate from the advanced options widget through `MainWindow._apply_locale_to_all`.

### Threading model

Long operations never run on the UI thread. `MainWindow` spins up a `QThread`, moves a `BookletWorker` onto it, and reacts to the worker's signals. When changing load/save behavior, keep the work inside the worker and surface results only through those signals.

### Translations (i18n)

The app uses Qt Linguist. All user-facing GUI strings are wrapped in `self.tr("...")`; `main.py` installs a `QTranslator` at startup that loads `src/assets/i18n/pdfbooklet_<locale>.qm` for the system locale, falling back to the English source if absent. Workflow and contributor guide: `docs/TRANSLATING.md`; regenerate the `.ts` template with `scripts/update_translations.sh`. **When adding GUI strings, wrap them in `tr()`.** **Never wrap text that doubles as a logic key** — combo boxes whose value drives behavior must carry a stable value via `addItem(self.tr("Display"), "key")` and be read with `currentData()` (see `general_options_widget.py`). Logic-tier code must not call `tr()`; surface user text at the GUI boundary. Currently untranslated by design: unit symbols (mm/in), DPI numbers, and the locale-picker names (the last deferred — its text is still a logic/persistence key).
