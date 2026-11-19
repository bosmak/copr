# scalpel — https://github.com/scalpelpoe/scalpel

[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL--3.0--only-blue.svg)](https://github.com/scalpelpoe/scalpel/blob/main/LICENSE)

Overlay for Path of Exile: it edits the loot filter of the game while
it runs, price checks the items on the screen, audits the economy of
the league and generates the regex of the item filters.

## Setup

Nothing to do — the application is installed with its desktop entry and
its icon:

```sh
sudo dnf install scalpel
```

Then launch it from the menu of the desktop, or with:

```sh
scalpel
```

## Files

| File | Purpose |
|---|---|
| `scalpel` | The launcher of the application |
| `/usr/libexec/scalpel/` | The runtime of the application (Electron) and its data |
| `scalpel.desktop` | The desktop entry |

## Notes

The application is built from the AppImage published by upstream: the
runtime and the data of the application are the very same ones the
AppImage ships. It is unpacked and installed under `/usr/libexec`,
because the runtime looks for its data in the `resources` directory next
to the binary — the layout of the AppImage is kept, so the application
finds its data wherever it is installed.

Fedora ships no Electron runtime, so the one of the AppImage is
installed with the application. It is the reason of the size of the
package.

The in-app updater does nothing here: `electron-updater` only works
when the `APPIMAGE` environment variable is set, and it is not. The
application is updated by the package manager.

The Chromium sandbox uses the unprivileged user namespaces of the
kernel, and the setuid helper installed next to the runtime when they
are not available.

The application cannot be run as root: Chromium does not support it,
and the launcher refuses it instead of starting a broken window.

The overlay window of the application is an X11 one: on a Wayland
session, the runtime detects the platform by itself, and it can be
forced with:

```sh
SCALPEL_OZONE_PLATFORM=x11 scalpel
```

The global hotkeys of the application are read by `uiohook`, which
needs the X11 test extension: it is a dependency of the package.
