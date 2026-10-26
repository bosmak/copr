# designcraft — https://github.com/storytold/designcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/designcraft/blob/main/LICENSE)

Open-source page layout and publishing app

DesignCraft is an open-source page layout and publishing application: lay out magazines, books and print documents with pages, frames, styles and a grid, then export to PDF and other formats.

## Setup

After `sudo dnf install designcraft` there is nothing to configure: the
application shows up in your app menu and the `.designcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
designcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `designcraft` | The desktop application |
| `designcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.designcraft.desktop` | Desktop entry |
| `ai.storyteller.designcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.designcraft.xml` | The `.designcraft` MIME type |
| `ai.storyteller.designcraft.png` | Application icon (PNG) |
| `ai.storyteller.designcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
