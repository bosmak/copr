# xwayland-satellite — https://github.com/Supreeeme/xwayland-satellite

[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](https://github.com/Supreeeme/xwayland-satellite/blob/main/LICENSE)

Rootless Xwayland integration for Wayland compositors.

xwayland-satellite grants rootless Xwayland integration to any Wayland
compositor implementing `xdg_wm_base` and `viewporter`. It is particularly
useful for compositors that do not want to implement rootless Xwayland
support themselves: satellite acts as the X window manager and hosts the
Xwayland server inside the Wayland session.

The package builds the upstream sources with the `systemd` and `fontconfig`
features enabled: satellite notifies systemd when Xwayland is up, and the
decoration font is loaded from the system instead of being embedded in the
binary.

## Setup

After `sudo dnf install xwayland-satellite` there is nothing to configure if
your compositor starts satellite on its own — some compositors integrate it
directly.

Otherwise, enable the user service that starts it with the graphical
session:

```sh
systemctl --user enable --now xwayland-satellite.service
```

The service is a *user* service, so it is controlled with `systemctl --user`:

```sh
systemctl --user status xwayland-satellite.service
journalctl --user -u xwayland-satellite.service -f
```

Satellite has to be started before any X11 application, otherwise the
application talks to the Xwayland server of the compositor (or to nothing at
all).

The compositor must implement the core Wayland protocols, `xdg_shell` and
`viewporter`. Optionally, satellite makes use of the Linux dmabuf, XDG
activation, XDG decoration, XDG foreign, pointer constraints, primary
selection, tablet input and fractional scale protocols.

Run the binary by hand with `RUST_LOG=debug` to see what it is doing:

```sh
RUST_LOG=debug xwayland-satellite
```

## Files

| File | Purpose |
|---|---|
| `xwayland-satellite` | The satellite itself — an X window manager that hosts Xwayland |
| `xwayland-satellite.service` | Systemd user service that starts it with the graphical session |
| `xwayland-satellite.1` | Manual page |
| `LICENSE` | Upstream's license (MPL-2.0) |
| `README.md` | Upstream's README |
