# pdfcraft — https://github.com/storytold/pdfcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/pdfcraft/blob/main/LICENSE)

Open-source PDF workbench: read, comment, fill and sign

PdfCraft is an open-source PDF workbench. Read, comment on, fill in and sign PDFs; organize, combine and split pages; edit, redact, protect and export documents.

## Setup

After `sudo dnf install pdfcraft` there is nothing to configure: the
application shows up in your app menu and the `.pdfcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
pdfcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `pdfcraft` | The desktop application |
| `pdfcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.pdfcraft.desktop` | Desktop entry |
| `ai.storyteller.pdfcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.pdfcraft.xml` | The `.pdfcraft` MIME type |
| `ai.storyteller.pdfcraft.png` | Application icon (PNG) |
| `ai.storyteller.pdfcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `NOTICE` | Attribution notice |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
| `ATTRIBUTION.txt` | OCR model used by the app |
| `text-detection.rten` | OCR model used by the app |
| `text-detection.rten.LICENCE.txt` | OCR model used by the app |
| `text-recognition.rten` | OCR model used by the app |
| `text-recognition.rten.LICENCE.txt` | OCR model used by the app |
