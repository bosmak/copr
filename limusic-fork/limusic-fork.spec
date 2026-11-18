%global commit c0a3ca36cbb4734c1b1a79ebc052993c0e23c4c1

Name:           limusic-fork
Version:        1.4.0~rc.10
Release:        1%{?dist}
Summary:        Desktop client for YouTube Music with casting support
License:        GPL-3.0-or-later
URL:            https://github.com/bosmak/limusic/tree/feature/cast
# The package follows a development branch of the fork. The commit is
# pinned so that a rebuild of the same SRPM always uses the same source.
Source0:        https://github.com/bosmak/limusic/archive/%{commit}.tar.gz
# The Rust crates, the built frontend and the patched IPADIC crate are
# staged together, so the RPM build does not need network access.
Source1:        limusic-fork-vendor.tar.xz
# Lindera embeds IPADIC in the binary for Japanese romanization.
Source2:        https://github.com/lindera-morphology/mecab-ipadic/archive/refs/tags/2.7.0-20070801.tar.gz
# The BotGuard runtime uses the prebuilt V8 static library.
Source3:        https://github.com/denoland/rusty_v8/releases/download/v130.0.7/librusty_v8_release_x86_64-unknown-linux-gnu.a.gz
Source4:        limusic-fork.desktop
# Give the fork its own application identity and disable the upstream
# self-updater, which would otherwise replace the fork with upstream builds.
Patch1:         limusic-fork.patch

BuildRequires:  cargo-rpm-macros
BuildRequires:  gcc-c++
BuildRequires:  gtk3-devel
BuildRequires:  libappindicator-gtk3-devel
BuildRequires:  librsvg2-devel
BuildRequires:  mpv-devel
BuildRequires:  openssl-devel
BuildRequires:  pkgconf-pkg-config
BuildRequires:  webkit2gtk4.1-devel

# The GUI stack is loaded at runtime, so rpm's ELF dependency detection
# cannot see all of it.
Requires:       libappindicator-gtk3
Requires:       mpv-libs
Requires:       webkit2gtk4.1
Requires:       gtk3

# The prebuilt V8 library is available for x86_64 only.
ExclusiveArch:  x86_64

%description
Limusic is a desktop client for YouTube Music written in Rust with
Tauri. It talks to the internal API of YouTube directly and plays the
audio through libmpv, so there is no browser runtime and no advertisement
in the audio.

This package builds the feature/cast branch of Gustavo Bosmak's fork.
In addition to the upstream playback, lyrics and scrobbling features,
it can send the current queue to Chromecast, Google Home and DLNA
renderers found on the local network.

The package installs a separate executable, desktop entry and icon, so
it can be installed alongside the regular limusic package.

%prep
%autosetup -n limusic-%{commit} -p1

# The vendor tarball contains the Rust crates, the compiled frontend
# assets and the local copy of the patched IPADIC crate.
tar -xf %{SOURCE1}

# Point cargo at the vendored dependencies and use the release profile of
# the RPM macros.
%cargo_prep -v vendor

# The patched crate is a path dependency, so cargo does not verify the
# checksum of the original vendored copy.
cat >> .cargo/config.toml <<'EOF'
[patch.crates-io]
lindera-ipadic = { path = "patched/lindera-ipadic" }
EOF

# Verify the two external build inputs before using them.
echo "099e46e80d55e7c0d6906783aff713748e1ae90f46c5ef96ec153bbf09bf5550  %{SOURCE2}" | sha256sum -c -
echo "a6476cb94e9b0247081c465424eb793d77732b8db80848132d78cbb50f34b75d  %{SOURCE3}" | sha256sum -c -

%build
# These inputs are consumed by the build scripts of lindera-ipadic and
# v8; neither build may reach the network.
export LINDERA_IPADIC_ARCHIVE=%{SOURCE2}
export RUSTY_V8_ARCHIVE=%{SOURCE3}
# The source is a Cargo workspace, so the package-level cargo-rpm-macros
# command cannot select src-tauri directly. Calling cargo without
# RUSTC_BOOTSTRAP also keeps rustix 0.37 from enabling compiler attributes
# that current Rust releases reject.
CARGO_HOME=.cargo RUSTFLAGS='%{build_rustflags}' /usr/bin/cargo build --profile rpm --manifest-path src-tauri/Cargo.toml

%install
install -Dm755 target/rpm/limusic-app %{buildroot}%{_bindir}/limusic-fork-app
install -Dm644 %{SOURCE4} %{buildroot}%{_datadir}/applications/limusic-fork.desktop
install -Dm644 src-tauri/icons/32x32.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/limusic-fork.png
install -Dm644 src-tauri/icons/64x64.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/limusic-fork.png
install -Dm644 src-tauri/icons/128x128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/limusic-fork.png
install -Dm644 src-tauri/icons/128x128@2x.png %{buildroot}%{_datadir}/icons/hicolor/256x256@2/apps/limusic-fork.png
install -Dm644 src-tauri/icons/icon.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/limusic-fork.png
install -Dm644 LICENSE %{buildroot}%{_licensedir}/limusic-fork/LICENSE
install -Dm644 README.md %{buildroot}%{_docdir}/limusic-fork/README.md

%post
# Refresh the desktop entry and the icon cache. Every helper is optional,
# so a missing one is simply skipped.
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q %{_datadir}/applications || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f %{_datadir}/icons/hicolor || :
fi

%postun
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q %{_datadir}/applications || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f %{_datadir}/icons/hicolor || :
fi

%files
%license %{_licensedir}/limusic-fork/LICENSE
%doc %{_docdir}/limusic-fork/README.md
%{_bindir}/limusic-fork-app
%{_datadir}/applications/limusic-fork.desktop
%{_datadir}/icons/hicolor/*/apps/limusic-fork.png

%changelog
* Wed Nov 18 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 1.4.0~rc.10-1
- initial COPR package built from the feature/cast fork branch
- upstream commit: c0a3ca36cbb4734c1b1a79ebc052993c0e23c4c1
