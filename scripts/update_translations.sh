#!/usr/bin/env bash
# PDFBooklet/scripts/update_translations.sh
#
# Regenerate the translation template (.ts) from the source code, and optionally
# compile any .ts files into runtime .qm files.
#
# Usage:
#   ./scripts/update_translations.sh            # extract strings -> pdfbooklet.ts
#   ./scripts/update_translations.sh --release  # also compile *.ts -> *.qm
#
# Requirements:
#   pylupdate6  (ships with PyQt6 — already in requirements-dev.txt)
#   lrelease    (only for --release; ships with Qt Linguist / qt6-l10n-tools)
set -euo pipefail

cd "$(dirname "$0")/.."

I18N_DIR="src/assets/i18n"
TEMPLATE="$I18N_DIR/pdfbooklet.ts"

mkdir -p "$I18N_DIR"

# All source files that contain tr() strings.
SOURCES=$(find main.py src/gui -name '*.py')

echo "Extracting strings -> $TEMPLATE"
pylupdate6 $SOURCES -ts "$TEMPLATE"

if [[ "${1:-}" == "--release" ]]; then
    if ! command -v lrelease >/dev/null 2>&1; then
        echo "ERROR: lrelease not found. Install Qt Linguist tools (qt6-l10n-tools)," >&2
        echo "       or use Qt Linguist's 'File > Release' to produce the .qm." >&2
        exit 1
    fi
    for ts in "$I18N_DIR"/*.ts; do
        [[ -e "$ts" ]] || continue
        echo "Compiling $ts -> ${ts%.ts}.qm"
        lrelease "$ts"
    done
fi

echo "Done."
