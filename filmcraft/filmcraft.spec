%global debug_package %{nil}
# Upstream ships prebuilt, already-stripped binaries. Re-running strip on
# them would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binaries bit-identical.
%global __strip /bin/true

Name:           filmcraft
Version:        0.13.0
Release:        1%{?dist}
Summary:        Open-source video editor: edit video, color and sound
License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/filmcraft
# Upstream publishes a prebuilt RPM for Linux. We rebundle its payload:
# the very same binaries and desktop integration, repacked with Fedora's
# directory layout (licenses under /usr/share/licenses, docs under
# /usr/share/doc) so the app can be installed straight from this project.
Source0:        https://github.com/storytold/filmcraft/releases/download/v%{version}/filmcraft-%{version}-linux-x86_64.rpm
# Upstream's checksum list, used in the prep section to verify Source0.
Source1:        https://github.com/storytold/filmcraft/releases/download/v%{version}/SHA256SUMS.txt

# The GUI stack (winit/xkbcommon) is dlopen()ed at runtime, so rpm's
# automatic ELF dependency detection does not see it. Upstream's own RPM
# requires these explicitly, so we do the same.
Requires:       glibc >= 2.35
Requires:       libxkbcommon
Requires:       (vulkan-loader or mesa-libEGL)
Requires:       alsa-lib

# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64

%description
FilmCraft is an open-source, native video editor. Edit video, color and sound on a timeline, with clips, transitions, titles and effects.

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
install -Dm755 payload/usr/bin/filmcraft %{buildroot}%{_bindir}/filmcraft
install -Dm755 payload/usr/bin/filmcraft-cli %{buildroot}%{_bindir}/filmcraft-cli
install -Dm644 payload/usr/share/applications/ai.storyteller.filmcraft.desktop %{buildroot}%{_datadir}/applications/ai.storyteller.filmcraft.desktop
install -Dm644 payload/usr/share/doc/filmcraft/LICENSE-APACHE %{buildroot}%{_licensedir}/filmcraft/LICENSE-APACHE
install -Dm644 payload/usr/share/doc/filmcraft/LICENSE-MIT %{buildroot}%{_licensedir}/filmcraft/LICENSE-MIT
install -Dm644 payload/usr/share/doc/filmcraft/OFL-biz-ud-mincho.txt %{buildroot}%{_licensedir}/filmcraft/OFL-biz-ud-mincho.txt
install -Dm644 payload/usr/share/doc/filmcraft/OFL-biz-ud-pgothic.txt %{buildroot}%{_licensedir}/filmcraft/OFL-biz-ud-pgothic.txt
install -Dm644 payload/usr/share/doc/filmcraft/OFL-noto-sans-arabic.txt %{buildroot}%{_licensedir}/filmcraft/OFL-noto-sans-arabic.txt
install -Dm644 payload/usr/share/doc/filmcraft/OFL-noto-sans-cjk-sc.txt %{buildroot}%{_licensedir}/filmcraft/OFL-noto-sans-cjk-sc.txt
install -Dm644 payload/usr/share/doc/filmcraft/OFL-noto-sans-georgian.txt %{buildroot}%{_licensedir}/filmcraft/OFL-noto-sans-georgian.txt
install -Dm644 payload/usr/share/doc/filmcraft/OFL-noto-sans-thai.txt %{buildroot}%{_licensedir}/filmcraft/OFL-noto-sans-thai.txt
install -Dm644 payload/usr/share/doc/filmcraft/OFL-shippori-mincho.txt %{buildroot}%{_licensedir}/filmcraft/OFL-shippori-mincho.txt
install -Dm644 payload/usr/share/doc/filmcraft/README.md %{buildroot}%{_docdir}/filmcraft/README.md
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/ai.storyteller.filmcraft.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.storyteller.filmcraft.png
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/ai.storyteller.filmcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.storyteller.filmcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/16x16/apps/ai.storyteller.filmcraft.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/ai.storyteller.filmcraft.png
install -Dm644 payload/usr/share/icons/hicolor/16x16/apps/ai.storyteller.filmcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/ai.storyteller.filmcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/24x24/apps/ai.storyteller.filmcraft.png %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/ai.storyteller.filmcraft.png
install -Dm644 payload/usr/share/icons/hicolor/24x24/apps/ai.storyteller.filmcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/ai.storyteller.filmcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/256x256/apps/ai.storyteller.filmcraft.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.storyteller.filmcraft.png
install -Dm644 payload/usr/share/icons/hicolor/256x256/apps/ai.storyteller.filmcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.storyteller.filmcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/ai.storyteller.filmcraft.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.storyteller.filmcraft.png
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/ai.storyteller.filmcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.storyteller.filmcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/48x48/apps/ai.storyteller.filmcraft.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/ai.storyteller.filmcraft.png
install -Dm644 payload/usr/share/icons/hicolor/48x48/apps/ai.storyteller.filmcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/ai.storyteller.filmcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/ai.storyteller.filmcraft.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.storyteller.filmcraft.png
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/ai.storyteller.filmcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.storyteller.filmcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/ai.storyteller.filmcraft.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.storyteller.filmcraft.png
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/ai.storyteller.filmcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.storyteller.filmcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/scalable/apps/ai.storyteller.filmcraft.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.filmcraft.svg
install -Dm644 payload/usr/share/icons/hicolor/scalable/apps/ai.storyteller.filmcraft.svg.attribution %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.filmcraft.svg.attribution
install -Dm644 payload/usr/share/metainfo/ai.storyteller.filmcraft.metainfo.xml %{buildroot}%{_datadir}/metainfo/ai.storyteller.filmcraft.metainfo.xml
install -Dm644 payload/usr/share/mime/packages/ai.storyteller.filmcraft.xml %{buildroot}%{_datadir}/mime/packages/ai.storyteller.filmcraft.xml

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
%license %{_licensedir}/filmcraft/LICENSE-APACHE
%license %{_licensedir}/filmcraft/LICENSE-MIT
%license %{_licensedir}/filmcraft/OFL-*
%doc %{_docdir}/filmcraft/README.md
%{_bindir}/filmcraft
%{_bindir}/filmcraft-cli
%{_datadir}/applications/ai.storyteller.filmcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.filmcraft.png
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.filmcraft.png.attribution
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.filmcraft.svg
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.filmcraft.svg.attribution
%{_datadir}/metainfo/ai.storyteller.filmcraft.metainfo.xml
%{_datadir}/mime/packages/ai.storyteller.filmcraft.xml

%changelog
* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.13.0-1
- update to 0.13.0

* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.12.0-1
- initial COPR package (rebundle of the upstream RPM)
