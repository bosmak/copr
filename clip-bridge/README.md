# clip-bridge — https://github.com/noctisynth/clip-bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/noctisynth/clip-bridge/blob/main/LICENSE)

Sync your X11 and Wayland clipboard seamlessly.

Just run `clip-bridge` once and it bridges the two — copy in X11, paste in Wayland; copy in Wayland, paste in X11. Useful when running a Wayland compositor with X11 apps (or vice versa) that don't share a clipboard by default.

## Files

| File | Purpose |
|---|---|
| `clip-bridge` | The binary — bridges X11 and Wayland clipboard event streams |
| `clip-bridge.service` | systemd user unit; `systemctl --user enable --now clip-bridge.service` to start |
| `LICENSE` | MIT |

