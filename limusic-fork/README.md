# limusic-fork — https://github.com/bosmak/limusic/tree/feature/cast

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](https://github.com/bosmak/limusic/blob/feature/cast/LICENSE)

Desktop client for YouTube Music, built from the `feature/cast` branch of
Gustavo Bosmak's fork.

Limusic talks to the internal API of YouTube directly and plays audio through
libmpv: no browser runtime, no backend server, and no ads in the audio. The
fork adds casting to Chromecast, Google Home and DLNA renderers discovered on
the local network.

This package is built from source. It installs a separate executable, desktop
entry and icon, so it can coexist with the regular `limusic` package. It
keeps the application identity of the upstream application, so the fork is
the same application: it shares the settings, the session and the logs with
the upstream `limusic` package. Its self-updater is disabled, so it never
replaces the fork with an upstream build.

## Setup

```sh
sudo dnf copr enable bosmak/copr
sudo dnf install limusic-fork
```

The application appears in the app menu as **Limusic Fork**. Its executable is
`/usr/bin/limusic-fork-app`.

The packaging repository checks the fork's `feature/cast` branch daily. When
it changes, a pull request updates the pinned source commit; merging it
rebuilds and publishes the package to COPR.

The dependencies are installed with the package: `mpv-libs` plays the audio,
`webkit2gtk4.1` renders the interface and `libappindicator-gtk3` provides the
tray icon.

Sign in to YouTube Music from the app itself, or paste the cookies of a
session that is already signed in. ListenBrainz scrobbling is configured in the
app's settings. Last.fm needs API credentials at build time; the package does
not distribute them, so Last.fm reports itself as unconfigured unless the
fork source supplies them.

## Files

| File | Purpose |
|---|---|
| `limusic-fork-app` | The desktop application |
| `limusic-fork.desktop` | Desktop entry |
| `limusic-fork.png` | Application icon |
| `LICENSE` | GPL-3.0 license |
