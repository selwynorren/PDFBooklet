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
pytest tests/test_imposition.py      # run the pure-logic layout tests
```

Tests currently cover only `booklet_layout.py` (pure logic, no Qt/I/O). Preview/save transform math is not yet under test.

Build the distributable AppImage with the full PyInstaller + appimagetool sequence in the `Build & Packaging Instructions` file (it bundles `LICENSE`, `docs/`, and `src/assets/` into a one-file executable, then wraps it in an AppDir). `PDFBooklet.spec` is the generated PyInstaller spec.

Note: `.gitignore` excludes `build/`, `dist/`, `*.spec`, `*.AppImage`, and `Build & Packaging Instructions` — packaging artifacts are not tracked.

## Architecture

Entry point is the top-level `main.py`, which fixes `sys.path`, sets `QApplication` org/name (for `QSettings`), and launches `src/gui/main_window.py`. The codebase splits cleanly into a **logic layer** (`src/logic/`, no Qt UI) and a **GUI layer** (`src/gui/`).

### Two PDF libraries, two jobs

This is the most important thing to understand before touching PDF code:

- **PyMuPDF (`fitz`)** — used **only** for fast preview rendering and metadata/page-size reads (`pdf_renderer.py`, plus `main_window.py`). The renderer keeps the document open (stateful mode) for repeated fast rendering.
- **pypdf** — used **only** for saving output (`pdf_saver.py`). Saves are **vector-preserving**; transforms (shift/rotate/scale/flip) are applied as pypdf `Transformation` matrices at save time, not rasterized.

All PDF work goes through `pdf_renderer` (preview) and `pdf_saver` (output). The old `PyPDF2`-based `pdf_handler.py` has been removed — do not reintroduce PyPDF2 (it is deprecated; `pypdf` is its successor).

### Logic layer (`src/logic/`)

- **`booklet_processor.py`** — the coordinator. Holds state (PDF path, page count, original page size) and delegates: layout to `BookletLayout`, preview to `PDFRenderer`, saving to `PDFSaver`, transforms to `PageTransformManager`. The GUI talks mostly to this class.
- **`booklet_layout.py`** — pure layout generation. Produces a `LayoutMap` (list of page-index pairs/singles) for booklet/calendar/single modes. No I/O, no rendering. Handles booklet padding (pads to a multiple of 4).
- **`page_transforms.py`** — `Transform` dataclass (all measurements in **mm**, scale in **percent**, rotation in **degrees**) plus `PageTransformManager`, whose `get_transform_for_page()` compounds three layers (global + even/odd domain + per-page override) into the final `Transform`. `create_transform_from_gui()` bridges GUI widget values into a `Transform`.
- **`pdf_renderer.py` / `pdf_saver.py`** — rendering and saving as described above.
- **`image_downscaler.py`** — optional image downsampling applied during save to shrink output file size (target DPI based).
- **`booklet_worker.py`** — a `QObject` worker run on a `QThread` for the two heavy operations: **loading** a PDF (constructs a `BookletProcessor`) and **saving** a booklet. Mode is chosen by which constructor args are set (`pdf_path` alone → load; `processor` + `output_path` → save). Communicates via `processing_finished` / `processing_failed` / `progress_updated` signals.
- **`unit_converter.py`** — mm/inch conversion helpers (the app supports both unit systems and locale switching).

### GUI layer (`src/gui/`)

`main_window.py` (`MainWindow`) is the orchestrator: it owns the `BookletProcessor`, manages the load/save `QThread`s, persists UI state via `QSettings("PDFBooklet", "PDFBooklet")`, and assembles the tabbed options panels — `GeneralOptionsWidget`, `GlobalOptionsWidget`, `PageOptionsWidget`, `AdvancedOptionsWidget` — alongside the preview (`PreviewViewerWidget` / `PreviewEmptyWidget`) and `ControlWidget`. Locale changes propagate from the advanced options widget through `MainWindow._apply_locale_to_all`.

### Threading model

Long operations never run on the UI thread. `MainWindow` spins up a `QThread`, moves a `BookletWorker` onto it, and reacts to the worker's signals. When changing load/save behavior, keep the work inside the worker and surface results only through those signals.
