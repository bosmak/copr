# photocraft — https://github.com/storytold/photocraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/photocraft/blob/main/LICENSE)

Open-source image editor with familiar, professional tools

PhotoCraft is an open-source, native image editor with the familiar menus, shortcuts, panels and tools professionals expect: layers, masks, adjustment layers, layer styles, type and brushes.

## Setup

After `sudo dnf install photocraft` there is nothing to configure: the
application shows up in your app menu and the `.photocraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
photocraft-cli
```

## Files

| File | Purpose |
|---|---|
| `photocraft` | The desktop application |
| `photocraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.photocraft.desktop` | Desktop entry |
| `ai.storyteller.photocraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.photocraft.xml` | The `.photocraft` MIME type |
| `ai.storyteller.photocraft.png` | Application icon (PNG) |
| `ai.storyteller.photocraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
