# wordcraft — https://github.com/storytold/wordcraft

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://github.com/storytold/wordcraft/blob/main/LICENSE)

Open-source word processor that works the way Word users expect

WordCraft is a fast, open-source word processor with a familiar ribbon: styles, tables, track changes, references, mail merge, and .docx, PDF, ODT, RTF, HTML and Markdown files. It can be driven by AI agents over MCP.

## Setup

After `sudo dnf install wordcraft` there is nothing to configure: the
application shows up in your app menu and the `.wordcraft` files open with
it.

The post-install script refreshes the desktop entry, the MIME database and
the icon cache, so the launcher and the file associations are ready right
away.

A headless command line is installed as well, for scripting the app:

```sh
wordcraft-cli
```

## Files

| File | Purpose |
|---|---|
| `wordcraft` | The desktop application |
| `wordcraft-cli` | Headless command line — every action is a command |
| `ai.storyteller.wordcraft.desktop` | Desktop entry |
| `ai.storyteller.wordcraft.metainfo.xml` | AppStream metadata |
| `ai.storyteller.wordcraft.xml` | The `.wordcraft` MIME type |
| `ai.storyteller.wordcraft.png` | Application icon (PNG) |
| `ai.storyteller.wordcraft.svg` | Application icon (SVG) |
| `LICENSE-APACHE` | Apache-2.0 license |
| `LICENSE-MIT` | MIT license |
| `OFL-*.txt` | SIL Open Font License texts of the bundled fonts |
| `README.md` | Upstream's README |
