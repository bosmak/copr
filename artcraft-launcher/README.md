# artcraft-launcher — https://github.com/storytold/craft-launcher

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/craft-launcher/blob/main/LICENSE)

Install, update and launch the Craft App Suite

The ArtCraft Launcher installs, updates and opens every app in the Craft
App Suite: PhotoCraft, LightCraft, FilmCraft, DesignCraft, VectorCraft,
PdfCraft, EffectCraft, WordCraft, DeckCraft, GridCraft, CADCraft,
SoundCraft and FigCraft.

It picks the right build for your computer and keeps it up to date, so you
do not have to download every app by hand.

## Setup

After `sudo dnf install artcraft-launcher` there is nothing to configure: the
launcher shows up in your app menu.

The post-install script refreshes the desktop entry and the icon cache, so
the launcher is ready right away.

## Files

| File | Purpose |
|---|---|
| `artcraft-launcher` | The launcher |
| `ai.storyteller.artcraft-launcher.desktop` | Desktop entry |
| `ai.storyteller.artcraft-launcher.metainfo.xml` | AppStream metadata |
| `ai.storyteller.artcraft-launcher.png` | Application icon (PNG) |
| `ai.storyteller.artcraft-launcher.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `NOTICE` | Attribution notice |
| `README.md` | Upstream's README |
| `ATTRIBUTION.md` | Upstream's attribution list |
