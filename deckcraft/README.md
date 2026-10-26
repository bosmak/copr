# deckcraft — https://github.com/storytold/deckcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/deckcraft/blob/main/LICENSE)

Open-source presentation app that works the way PowerPoint users expect

DeckCraft builds presentations and slide shows: themes, layouts, shapes, pictures, tables, charts, transitions and animations. It opens and saves PowerPoint (.pptx) files and presents them full screen with a presenter view.

## Setup

After `sudo dnf install deckcraft` there is nothing to configure: the
application shows up in your app menu and the `.deckcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
deckcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `deckcraft` | The desktop application |
| `deckcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.deckcraft.desktop` | Desktop entry |
| `ai.storyteller.deckcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.deckcraft.xml` | The `.deckcraft` MIME type |
| `ai.storyteller.deckcraft.png` | Application icon (PNG) |
| `ai.storyteller.deckcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
