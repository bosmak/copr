%global debug_package %{nil}
# Upstream ships prebuilt, already-stripped binaries. Re-running strip on
# them would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binaries bit-identical.
%global __strip /bin/true

Name:           artcraft-launcher
Version:        0.11.1
Release:        1%{?dist}
Summary:        Install, update and launch the Craft App Suite
License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/craft-launcher
# Upstream publishes a prebuilt RPM for Linux. We rebundle its payload:
# the very same binaries and desktop integration, repacked with Fedora's
# directory layout (licenses under /usr/share/licenses, docs under
# /usr/share/doc) so the app can be installed straight from this project.
Source0:        https://github.com/storytold/craft-launcher/releases/download/v%{version}/artcraft-launcher-%{version}-linux-x86_64.rpm
# Upstream's checksum list, used in the prep section to verify Source0.
Source1:        https://github.com/storytold/craft-launcher/releases/download/v%{version}/SHA256SUMS.txt

# The GUI stack (winit/xkbcommon) is dlopen()ed at runtime, so rpm's
# automatic ELF dependency detection does not see it. Upstream's own RPM
# requires these explicitly, so we do the same.
Requires:       glibc >= 2.35
Requires:       libxkbcommon
Requires:       libxkbcommon-x11
Requires:       libwayland-client
Requires:       libX11
Requires:       libX11-xcb
Requires:       libxcb
Requires:       libXcursor
Requires:       libXi
Requires:       (vulkan-loader or mesa-libEGL)

# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64

%description
The ArtCraft Launcher installs, updates and opens every app in the Craft
App Suite: PhotoCraft, LightCraft, FilmCraft, DesignCraft, VectorCraft,
PdfCraft, EffectCraft, WordCraft, DeckCraft, GridCraft, CADCraft,
SoundCraft and FigCraft.

It picks the right build for your computer and keeps it up to date, so you
do not have to download every app by hand.

%prep
# Verify the downloaded RPM against upstream's checksum list.
rpm_file=%{SOURCE0}
base=$(basename "$rpm_file")
expected=$(awk -v f="$base" '$2 == f { print $1 }' %{SOURCE1})
if [ -z "$expected" ]; then
    echo "No checksum for $base in %{SOURCE1}" >&2
    exit 1
fi
actual=$(sha256sum "$rpm_file" | awk '{ print $1 }')
if [ "$expected" != "$actual" ]; then
    echo "SHA256 mismatch for $base: expected $expected, got $actual" >&2
    exit 1
fi

# Unpack the upstream RPM payload. rpm2archive turns the RPM into a tar of
# its files, so we need neither cpio nor bsdtar to read it.
mkdir -p payload
rpm2archive -n %{SOURCE0} | tar -xf - -C payload

%build
# Nothing to build — we ship upstream's prebuilt binaries verbatim.

%install
install -Dm755 payload/usr/bin/artcraft-launcher %{buildroot}%{_bindir}/artcraft-launcher
install -Dm644 payload/usr/share/applications/ai.storyteller.artcraft-launcher.desktop %{buildroot}%{_datadir}/applications/ai.storyteller.artcraft-launcher.desktop
install -Dm644 payload/usr/share/doc/artcraft-launcher/ATTRIBUTION.md %{buildroot}%{_docdir}/artcraft-launcher/ATTRIBUTION.md
install -Dm644 payload/usr/share/doc/artcraft-launcher/LICENSE-APACHE %{buildroot}%{_licensedir}/artcraft-launcher/LICENSE-APACHE
install -Dm644 payload/usr/share/doc/artcraft-launcher/LICENSE-MIT %{buildroot}%{_licensedir}/artcraft-launcher/LICENSE-MIT
install -Dm644 payload/usr/share/doc/artcraft-launcher/NOTICE %{buildroot}%{_licensedir}/artcraft-launcher/NOTICE
install -Dm644 payload/usr/share/doc/artcraft-launcher/README.md %{buildroot}%{_docdir}/artcraft-launcher/README.md
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/ai.storyteller.artcraft-launcher.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.storyteller.artcraft-launcher.png
install -Dm644 payload/usr/share/icons/hicolor/16x16/apps/ai.storyteller.artcraft-launcher.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/ai.storyteller.artcraft-launcher.png
install -Dm644 payload/usr/share/icons/hicolor/24x24/apps/ai.storyteller.artcraft-launcher.png %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/ai.storyteller.artcraft-launcher.png
install -Dm644 payload/usr/share/icons/hicolor/256x256/apps/ai.storyteller.artcraft-launcher.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.storyteller.artcraft-launcher.png
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/ai.storyteller.artcraft-launcher.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.storyteller.artcraft-launcher.png
install -Dm644 payload/usr/share/icons/hicolor/48x48/apps/ai.storyteller.artcraft-launcher.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/ai.storyteller.artcraft-launcher.png
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/ai.storyteller.artcraft-launcher.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.storyteller.artcraft-launcher.png
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/ai.storyteller.artcraft-launcher.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.storyteller.artcraft-launcher.png
install -Dm644 payload/usr/share/icons/hicolor/scalable/apps/ai.storyteller.artcraft-launcher.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.artcraft-launcher.svg
install -Dm644 payload/usr/share/metainfo/ai.storyteller.artcraft-launcher.metainfo.xml %{buildroot}%{_datadir}/metainfo/ai.storyteller.artcraft-launcher.metainfo.xml

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
%license %{_licensedir}/artcraft-launcher/LICENSE-APACHE
%license %{_licensedir}/artcraft-launcher/LICENSE-MIT
%license %{_licensedir}/artcraft-launcher/NOTICE
%doc %{_docdir}/artcraft-launcher/ATTRIBUTION.md
%doc %{_docdir}/artcraft-launcher/README.md
%{_bindir}/artcraft-launcher
%{_datadir}/applications/ai.storyteller.artcraft-launcher.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.artcraft-launcher.png
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.artcraft-launcher.svg
%{_datadir}/metainfo/ai.storyteller.artcraft-launcher.metainfo.xml

%changelog
* Sat Oct 31 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 0.11.1-1
- update to 0.11.1

* Fri Oct 30 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 0.10.0-1
- update to 0.10.0

* Wed Oct 28 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 0.9.0-1
- update to 0.9.0

* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.8.1-1
- initial COPR package (rebundle of the upstream RPM)
