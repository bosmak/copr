# lightcraft — https://github.com/storytold/lightcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/lightcraft/blob/main/LICENSE)

Open-source photo library and raw developer

LightCraft is an open-source photo library and raw developer. Organise photos and develop raw files non-destructively, with a catalogue, ratings, collections and a non-destructive develop pipeline.

## Setup

After `sudo dnf install lightcraft` there is nothing to configure: the
application shows up in your app menu and the `.lightcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
lightcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `lightcraft` | The desktop application |
| `lightcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.lightcraft.desktop` | Desktop entry |
| `ai.storyteller.lightcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.lightcraft.xml` | The `.lightcraft` MIME type |
| `ai.storyteller.lightcraft.png` | Application icon (PNG) |
| `ai.storyteller.lightcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `NOTICE` | Attribution notice |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
