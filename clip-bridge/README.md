# clip-bridge — https://github.com/noctisynth/clip-bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/noctisynth/clip-bridge/blob/main/LICENSE)

Sync your X11 and Wayland clipboard seamlessly.

Just run `clip-bridge` once and it bridges the two — copy in X11, paste in Wayland; copy in Wayland, paste in X11. Useful when running a Wayland compositor with X11 apps (or vice versa) that don't share a clipboard by default.

## Setup

> **This is a systemd *user* service, not a system service.** Always
> manage it with `systemctl --user` — plain `systemctl` will not find
> it.

After `sudo dnf install clip-bridge`, the post-install script tries to
auto-enable the service for your active user session. If you installed
from inside a graphical session you're logged into, the service is
already enabled and will auto-start on every login. Otherwise (e.g.
installing over SSH, in a container, or via kickstart), you have to
enable it manually:

1. **Enable the user service** (auto-starts on every login):

   ```sh
   systemctl --user enable --now clip-bridge.service
   ```

2. **Or run the binary once** to try it (no auto-start, dies when you
   close the terminal):

   ```sh
   clip-bridge
   ```

Check it's running with:

```sh
systemctl --user status clip-bridge.service
```

## Files

| File | Purpose |
|---|---|
| `clip-bridge` | The binary — bridges X11 and Wayland clipboard event streams |
| `clip-bridge.service` | systemd user unit; `systemctl --user enable --now clip-bridge.service` to start |
| `LICENSE` | MIT |

