# limusic — https://github.com/SimoHypers/limusic

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](https://github.com/SimoHypers/limusic/blob/master/LICENSE)

Desktop client for YouTube Music.

Limusic talks to the internal API of YouTube directly and plays the audio
through libmpv: no browser runtime, no backend server, no ads in the audio.

It plays your library, the playlists and the recommendations, shows the
synchronized lyrics next to the album art, and scrobbles what you play to
Last.fm or to ListenBrainz. The music videos play where the artwork sits,
and the mini player and the theater mode keep the music playing while the
window shrinks or goes fullscreen.

This is a rebundle of the RPM published by upstream: the binary is the very
same one upstream ships.

## Setup

After `sudo dnf install limusic` there is nothing to configure: the
application shows up in your app menu and starts right away.

The dependencies come with the package: `mpv-libs` plays the audio,
`webkit2gtk4.1` renders the interface and `libappindicator-gtk3` puts the
icon in the tray.

Sign in to YouTube Music from the app itself (the button in the title bar),
or paste the cookies of a session that is already signed in. The scrobbling
to Last.fm and to ListenBrainz is configured in the settings of the app.

## Files

| File | Purpose |
|---|---|
| `limusic-app` | The binary — the desktop application |
| `limusic.desktop` | Desktop entry |
| `limusic-app.png` | Application icon (PNG, in the usual sizes) |
| `LICENSE` | GPL-3.0 license |
