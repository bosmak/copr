# figcraft — https://github.com/storytold/figcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/figcraft/blob/main/LICENSE)

Open-source interface design and prototyping tool

FigCraft is an open-source, native interface design and prototyping tool. Lay out screens on an infinite canvas with frames, auto layout and constraints, build reusable components and variants, and link screens into clickable prototypes.

## Setup

After `sudo dnf install figcraft` there is nothing to configure: the
application shows up in your app menu and the `.figcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
figcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `figcraft` | The desktop application |
| `figcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.figcraft.desktop` | Desktop entry |
| `ai.storyteller.figcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.figcraft.xml` | The `.figcraft` MIME type |
| `ai.storyteller.figcraft.png` | Application icon (PNG) |
| `ai.storyteller.figcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `NOTICE` | Attribution notice |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
