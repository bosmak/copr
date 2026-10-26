# soundcraft — https://github.com/storytold/soundcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/soundcraft/blob/main/LICENSE)

Open-source digital audio workstation: record, edit and mix

SoundCraft is an open-source, native digital audio workstation. Record, edit and mix multitrack audio and MIDI in Edit and Mix windows that work the way studio engineers expect.

## Setup

After `sudo dnf install soundcraft` there is nothing to configure: the
application shows up in your app menu and the `.soundcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
soundcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `soundcraft` | The desktop application |
| `soundcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.soundcraft.desktop` | Desktop entry |
| `ai.storyteller.soundcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.soundcraft.xml` | The `.soundcraft` MIME type |
| `ai.storyteller.soundcraft.png` | Application icon (PNG) |
| `ai.storyteller.soundcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `NOTICE` | Attribution notice |
| `README.md` | Upstream's README |
