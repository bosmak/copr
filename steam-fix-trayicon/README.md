# steam-fix-trayicon

Replacement Steam tray icon for Wayland desktops: **double click opens the
Steam window**, single click still opens Steam's own menu.

## Why

Steam's Linux tray icon is an AppIndicator (libappindicator / ayatana). The
panel host sends `Activate()` on every click and the indicator always answers
with Steam's popup menu, so the Steam window can never be opened from the
tray icon. That is Valve's own open feature request:

- [ValveSoftware/steam-for-linux#3519](https://github.com/ValveSoftware/steam-for-linux/issues/3519)
  — *"Double-click on the icon in the notification area should unhide"*
  (opened 2014, still open; a Valve dev replied: *"Steam doesn't control the
  behavior of that icon, that's abstracted via libappindicator"*)

No Steam or panel setting changes that. This package ships a small
StatusNotifierItem that does the right thing instead.

## Behaviour

| Action | Result |
|---|---|
| Single left click | Steam's **real menu** — recently played games, Store, Library, Community, Friends, Settings, Big Picture, SteamVR, Exit |
| Double left click | Opens / focuses the Steam window (`steam://open/main`) |
| Right click | Same menu |

The menu is proxied from Steam's own dbusmenu, so the recently played games
list is always current. The icon, tooltip and attention state are mirrored
from Steam's real indicator.

## Install

```sh
sudo dnf copr enable bosmak/copr
sudo dnf install steam-fix-trayicon
```

The post-install script enables and starts the user service for every
logged-in user and restarts the shell so the change takes effect right away.

> **This is a systemd *user* service, not a system service.** Always manage it
> with `systemctl --user` — plain `systemctl` will not find it.

```sh
systemctl --user status steam-fix-trayicon.service
```

## Requirements

- `python3-dbus`, `python3-gobject` (pulled in automatically)
- `quickshell` — recommended; it provides the tray IPC the shell uses to
  render the menu on a single click. Without it the icon and the double click
  still work, only the single-click menu is unavailable.
- A panel that supports StatusNotifierItem (DankMaterialShell, KDE, GNOME with
  the AppIndicator extension, …)

## Tuning

Override with environment variables in the unit file:

```ini
# /usr/lib/systemd/user/steam-fix-trayicon.service  (or a drop-in in
# ~/.config/systemd/user/steam-fix-trayicon.service.d/)
[Service]
Environment=STEAM_TRAY_DOUBLE_CLICK_MS=450   # max gap between the two clicks
Environment=STEAM_TRAY_MENU_DELAY_MS=280     # delay before the menu opens
Environment=STEAM_TRAY_WINDOW_URL=steam://open/main
```

Then `systemctl --user restart steam-fix-trayicon.service`.

## Uninstall / revert

```sh
sudo dnf remove steam-fix-trayicon
```

To keep the package but go back to Valve's original icon:

```sh
sudo rm /usr/lib/systemd/user/dms.service.d/99-steam-fix-trayicon.conf
systemctl --user daemon-reload
systemctl --user restart dms.service
systemctl --user disable --now steam-fix-trayicon.service
```

## Files

| File | Purpose |
|---|---|
| `/usr/bin/steam-fix-trayicon` | The indicator — a Python StatusNotifierItem |
| `/usr/lib/systemd/user/steam-fix-trayicon.service` | systemd user unit; `systemctl --user enable --now steam-fix-trayicon.service` to start |
| `/usr/lib/systemd/user/dms.service.d/99-steam-fix-trayicon.conf` | DankMaterialShell drop-in hiding Valve's original icon |
| `LICENSE` | MIT |
