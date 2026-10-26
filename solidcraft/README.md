# solidcraft — https://github.com/tangency-labs/solidcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/tangency-labs/solidcraft/blob/main/LICENSE)

Open-source parametric 3D CAD application

SolidCraft is an open-source parametric 3D CAD application written in Rust.
Sketch on a plane, constrain and dimension the sketch, turn profiles into
solids on a feature timeline, and change a parameter to watch the timeline
rebuild.

The package ships the desktop application (solidcraft), the headless command
line interface (solidcraft-cli) and its legacy alias (solvecraft-cli), plus
the desktop entry, the AppStream metadata and the .solidcraft MIME type.

This is a rebundle of the RPM published by upstream: the binaries are the
very same ones upstream ships.

## Setup

After `sudo dnf install solidcraft` there is nothing to configure: the
application shows up in your app menu and the `.solidcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
solidcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `solidcraft` | The desktop application |
| `solidcraft-cli` | Headless command line — every action is a command |
| `solvecraft-cli` | Legacy alias of the command line |
| `ai.storyteller.solidcraft.desktop` | Desktop entry |
| `ai.storyteller.solidcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.solidcraft.xml` | The `.solidcraft` MIME type |
| `ai.storyteller.solidcraft.png` | Application icon (PNG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `NOTICE` | Attribution notice |
| `README.md` | Upstream's README |
