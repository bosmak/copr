# vectorcraft — https://github.com/storytold/vectorcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/vectorcraft/blob/main/LICENSE)

Open-source vector illustration app

VectorCraft is an open-source vector illustration app. Draw with pen, shape and brush tools, style art with fills, strokes, gradients and live effects, lay out artboards and type, and open and save SVG and PDF.

## Setup

After `sudo dnf install vectorcraft` there is nothing to configure: the
application shows up in your app menu and the `.vectorcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
vectorcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `vectorcraft` | The desktop application |
| `vectorcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.vectorcraft.desktop` | Desktop entry |
| `ai.storyteller.vectorcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.vectorcraft.xml` | The `.vectorcraft` MIME type |
| `ai.storyteller.vectorcraft.png` | Application icon (PNG) |
| `ai.storyteller.vectorcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `NOTICE` | Attribution notice |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
| `licenses/` | Licenses of the bundled PDF backend |
