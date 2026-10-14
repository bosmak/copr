# pvpn — https://github.com/YourDoritos/pVPN

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](https://github.com/YourDoritos/pVPN/blob/main/LICENSE)

A fast, lightweight Proton VPN client for Linux with a terminal UI. Written in Go.

Daemon-based architecture — the VPN stays connected when you close the TUI. Works with NetworkManager, systemd-networkd + iwd, or bare setups — auto-detects your network stack.

Unlike the official Proton VPN Linux app, pVPN:

- Doesn't require NetworkManager — works on any network setup
- Supports Stealth protocol (WireGuard-over-TLS) — bypasses DPI and firewalls
- Runs as a lightweight daemon — no Electron, no Python, just Go binaries

## Files

| File | Purpose |
|---|---|
| `pvpnd` | Daemon — runs as root, owns the WireGuard interface, routes, nftables kill switch, and Proton session |
| `pvpn` | Terminal UI client — runs unprivileged, talks to the daemon over the `pvpn` group's Unix socket |
| `pvpnctl` | Scriptable CLI for `status`, `connect`, `disconnect`, etc. — same socket as the TUI |
| `pvpnd.service` | systemd unit that starts the daemon at boot, enabled automatically by dnf |
| `pvpn-preboot-killswitch.service` | Runs before network comes up; loads nftables rules that block all egress when the kill switch was enabled on the last session |
| `systemd-time-wait-sync.service.d/10-pvpn.conf` | Caps systemd-timesync's boot wait at 15s (instead of the 120s default) so the kill switch doesn't hold up NTP sync |
| `pvpn.sysusers.conf` | Creates the unprivileged `pvpn` system group on first install via systemd-sysusers |
