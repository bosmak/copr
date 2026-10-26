# effectcraft — https://github.com/storytold/effectcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/effectcraft/blob/main/LICENSE)

Open-source motion graphics and visual effects compositor

EffectCraft is an open-source motion graphics and visual effects compositor: layers with keyframes and a graph editor, masks and shapes, text animators, expressions, 3D cameras and lights, over 300 effects and a render queue, with GPU compositing.

## Setup

After `sudo dnf install effectcraft` there is nothing to configure: the
application shows up in your app menu and the `.effectcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
effectcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `effectcraft` | The desktop application |
| `effectcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.effectcraft.desktop` | Desktop entry |
| `ai.storyteller.effectcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.effectcraft.xml` | The `.effectcraft` MIME type |
| `ai.storyteller.effectcraft.png` | Application icon (PNG) |
| `ai.storyteller.effectcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `README.md` | Upstream's README |
