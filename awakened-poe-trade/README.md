# awakened-poe-trade — https://github.com/SnosMe/awakened-poe-trade

[![License: MIT AND BSD-3-Clause](https://img.shields.io/badge/License-MIT%20AND%20BSD--3--Clause-blue.svg)](https://github.com/SnosMe/awakened-poe-trade/blob/master/LICENSE)

Price checker for Path of Exile: it looks for the prices of the items
of the official trade API and of the community ones, so the price of a
drop can be known before picking it up.

## Setup

Nothing to do — the application is installed with its desktop entry and
its icon:

```sh
sudo dnf install awakened-poe-trade
```

Then launch it from the menu of the desktop, or with:

```sh
awakened-poe-trade
```

## Files

| File | Purpose |
|---|---|
| `awakened-poe-trade` | The launcher of the application |
| `/usr/libexec/awakened-poe-trade/` | The runtime of the application (Electron) and its data |
| `awakened-poe-trade.desktop` | The desktop entry |

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

On a Wayland session, the runtime detects the platform by itself. It
can be forced with:

```sh
AWAKENED_POE_TRADE_OZONE_PLATFORM=x11 awakened-poe-trade
```
