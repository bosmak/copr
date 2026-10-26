# cadcraft — https://github.com/storytold/cadcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/cadcraft/blob/main/LICENSE)

Open-source computer-aided design and drafting app

CADCraft is an open-source computer-aided design and drafting application with a familiar command line, object snaps, layers, dimensions, hatches and blocks. It opens and saves DXF and DWG drawings, exports SVG and PNG, and can be driven by AI agents over MCP.

## Setup

After `sudo dnf install cadcraft` there is nothing to configure: the
application shows up in your app menu and the `.cadcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
cadcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `cadcraft` | The desktop application |
| `cadcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.cadcraft.desktop` | Desktop entry |
| `ai.storyteller.cadcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.cadcraft.xml` | The `.cadcraft` MIME type |
| `ai.storyteller.cadcraft.png` | Application icon (PNG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
