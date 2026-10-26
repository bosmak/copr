# gridcraft — https://github.com/storytold/gridcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/gridcraft/blob/main/LICENSE)

Open-source spreadsheet that works the way Excel users expect

GridCraft is an open-source, native spreadsheet. It opens and saves .xlsx workbooks and CSV/TSV files, evaluates hundreds of worksheet functions, and formats, sorts, filters and charts your data.

## Setup

After `sudo dnf install gridcraft` there is nothing to configure: the
application shows up in your app menu and the `.gridcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
gridcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `gridcraft` | The desktop application |
| `gridcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.gridcraft.desktop` | Desktop entry |
| `ai.storyteller.gridcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.gridcraft.xml` | The `.gridcraft` MIME type |
| `ai.storyteller.gridcraft.png` | Application icon (PNG) |
| `ai.storyteller.gridcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
