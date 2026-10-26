# filmcraft — https://github.com/storytold/filmcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/filmcraft/blob/main/LICENSE)

Open-source video editor: edit video, color and sound

FilmCraft is an open-source, native video editor. Edit video, color and sound on a timeline, with clips, transitions, titles and effects.

## Setup

After `sudo dnf install filmcraft` there is nothing to configure: the
application shows up in your app menu and the `.filmcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
filmcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `filmcraft` | The desktop application |
| `filmcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.filmcraft.desktop` | Desktop entry |
| `ai.storyteller.filmcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.filmcraft.xml` | The `.filmcraft` MIME type |
| `ai.storyteller.filmcraft.png` | Application icon (PNG) |
| `ai.storyteller.filmcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
