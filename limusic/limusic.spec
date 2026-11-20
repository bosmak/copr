%global debug_package %{nil}
# Upstream ships prebuilt, already-stripped binaries. Re-running strip on
# them would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binaries bit-identical.
%global __strip /bin/true

Name:           limusic
Version:        1.4.1
Release:        1%{?dist}
Summary:        Desktop client for YouTube Music
License:        GPL-3.0-or-later
URL:            https://limusic.app
# Upstream publishes a prebuilt RPM for Linux. We rebundle its payload:
# the very same binaries and desktop integration, repacked with Fedora's
# directory layout (licenses under /usr/share/licenses, docs under
# /usr/share/doc) so the app can be installed straight from this project.
#
# The name of the asset carries the release of the RPM, so it has to be
# fixed here when upstream bumps it.
Source0:        https://github.com/SimoHypers/limusic/releases/download/v%{version}/limusic-%{version}-1.x86_64.rpm
# The upstream RPM ships no license, so the one of the tag is used.
Source1:        https://raw.githubusercontent.com/SimoHypers/limusic/v%{version}/LICENSE

# Upstream's own RPM requires its libraries explicitly, so we do the
# same: the sonames it lists are translated into the Fedora packages
# that provide them. Some of them are loaded with dlopen() at runtime,
# so rpm's automatic ELF dependency detection does not see them.
Requires:       libappindicator-gtk3
Requires:       mpv-libs
Requires:       libssl.so.3
Requires:       libcrypto.so.3
Requires:       webkit2gtk4.1
Requires:       gtk3

# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64

%description
Limusic is a desktop client for YouTube Music written in Rust with
Tauri. It talks to the internal API of YouTube directly and plays the
audio through libmpv, so there is no browser runtime and no
advertisement in the audio.

It plays your library, the playlists and the recommendations, shows
the synchronized lyrics next to the album art, and scrobbles what you
play to Last.fm or to ListenBrainz. The music videos play where the
artwork sits, and the mini player and the theater mode keep the music
playing while the window shrinks or goes fullscreen.

The package ships the desktop application, its desktop entry and its
icons. It is a rebundle of the RPM published by upstream: the binary is
the very same one upstream ships.

%prep
# Upstream publishes no checksum list for its releases, so the RPM is
# fetched over TLS from the official release page. Its digest is
# recorded in the changelog.

# Unpack the upstream RPM payload. rpm2archive turns the RPM into a tar of
# its files, so we need neither cpio nor bsdtar to read it.
mkdir -p payload
rpm2archive -n %{SOURCE0} | tar -xf - -C payload

# The upstream RPM ships no license, so the one of the tag is used.
install -Dm644 %{SOURCE1} payload/usr/share/doc/limusic/LICENSE

%build
# Nothing to build — we ship upstream's prebuilt binaries verbatim.

%install
install -Dm755 payload/usr/bin/limusic-app %{buildroot}%{_bindir}/limusic-app
install -Dm644 payload/usr/share/applications/limusic.desktop %{buildroot}%{_datadir}/applications/limusic.desktop
install -Dm644 payload/usr/share/doc/limusic/LICENSE %{buildroot}%{_licensedir}/limusic/LICENSE
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/limusic-app.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/limusic-app.png
install -Dm644 payload/usr/share/icons/hicolor/256x256@2/apps/limusic-app.png %{buildroot}%{_datadir}/icons/hicolor/256x256@2/apps/limusic-app.png
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/limusic-app.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/limusic-app.png
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/limusic-app.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/limusic-app.png
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/limusic-app.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/limusic-app.png

%post
# Refresh the desktop entry, the MIME database and the icon cache. Every
# helper is optional, so a missing one is simply skipped.
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q %{_datadir}/applications || :
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database %{_datadir}/mime || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f %{_datadir}/icons/hicolor || :
fi

%postun
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q %{_datadir}/applications || :
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database %{_datadir}/mime || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f %{_datadir}/icons/hicolor || :
fi

%files
%license %{_licensedir}/limusic/LICENSE
%{_bindir}/limusic-app
%{_datadir}/applications/limusic.desktop
%{_datadir}/icons/hicolor/*/apps/limusic-app.png

%changelog
* Fri Nov 20 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 1.4.1-1
- update to 1.4.1

* Thu Nov 19 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 1.4.0-1
- update to 1.4.0

* Mon Nov 16 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 1.3.0-1
- initial COPR package (rebundle of the upstream RPM)
- sha256 of the upstream RPM:
  cdb55cac6e34217699e88ab332c27cb331efa8c50785c76a408c913da2e0c3e6
