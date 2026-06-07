# Translating PDFBooklet

PDFBooklet is built to be translated. The interface ships in English, but every
user-facing string is translatable, and the app will automatically load a
translation that matches the user's system language if one is available.

**You do not need to be a programmer to translate PDFBooklet.** You need the free
**Qt Linguist** application and the project's translation template.

## What you'll work with

- `src/assets/i18n/pdfbooklet.ts` — the **template**: every English string in the
  app, ready to be translated. (`.ts` = Translation Source, an XML file.)
- `src/assets/i18n/pdfbooklet_<lang>.qm` — the **compiled** translation the app
  actually loads at runtime (e.g. `pdfbooklet_af.qm` for Afrikaans,
  `pdfbooklet_fr.qm` for French). `.qm` is generated from `.ts`.

The locale code follows the system language, e.g. `af` (Afrikaans), `fr` (French),
`de` (German), `zh` (Chinese). For region-specific variants use `fr_FR`, `pt_BR`, etc.

## How to translate (the easy way: Qt Linguist)

1. **Install Qt Linguist.**
   - Linux (Debian/Ubuntu/Mint): `sudo apt install qttools5-dev-tools` or
     `qt6-l10n-tools` (package name varies by distro).
   - Windows/macOS: install it from the Qt website or your package manager.

2. **Make your language file.** Copy the template to your language code:
   ```bash
   cp src/assets/i18n/pdfbooklet.ts src/assets/i18n/pdfbooklet_af.ts
   ```
   (replace `af` with your language code).

3. **Open it in Qt Linguist** (`File > Open`, pick your `pdfbooklet_<lang>.ts`).
   Qt Linguist will ask for the target language the first time — set it.

4. **Translate.** Work down the list, typing the translation for each English
   string and marking each as done (the green checkmark). Leave anything you're
   unsure about untranslated — the app falls back to English for those.

5. **Produce the runtime file.** In Qt Linguist choose **`File > Release`** to
   create `pdfbooklet_<lang>.qm` next to your `.ts`. (Or run
   `./scripts/update_translations.sh --release`.)

6. **Test it** by running the app with your system language set to that language,
   or just send us your `.ts` file — we'll compile and ship it.

## Submitting a translation

Send a pull request (or just email the file to the maintainer) containing your
`src/assets/i18n/pdfbooklet_<lang>.ts`. That's the source of truth; the `.qm` is
generated from it. We'll review and include it in the next release.

## Notes / things that are intentionally NOT translated

- **Unit symbols** (`mm`, `in`) and **DPI numbers** — these are universal.
- **Language names** in the in-app locale picker — left as-is for now.
- Format placeholders like `{0}`, `{1}` in a string **must be kept** in your
  translation (they get replaced with numbers/filenames at runtime). You may
  reorder them if your language needs a different word order.

## For maintainers: refreshing the template

When new English strings are added to the code, regenerate the template so
translators see them:

```bash
./scripts/update_translations.sh          # updates pdfbooklet.ts
./scripts/update_translations.sh --release  # also compiles *.ts -> *.qm
```

This runs `pylupdate6` (ships with PyQt6) over `main.py` and `src/gui/`. Existing
translations in each `.ts` are preserved; only new/changed strings are added.
