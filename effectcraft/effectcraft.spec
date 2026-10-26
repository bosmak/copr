%global debug_package %{nil}
# Upstream ships prebuilt, already-stripped binaries. Re-running strip on
# them would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binaries bit-identical.
%global __strip /bin/true

Name:           effectcraft
Version:        0.17.0
Release:        1%{?dist}
Summary:        Open-source motion graphics and visual effects compositor
License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/effectcraft
# Upstream publishes a prebuilt RPM for Linux. We rebundle its payload:
# the very same binaries and desktop integration, repacked with Fedora's
# directory layout (licenses under /usr/share/licenses, docs under
# /usr/share/doc) so the app can be installed straight from this project.
Source0:        https://github.com/storytold/effectcraft/releases/download/v%{version}/effectcraft-%{version}-linux-x86_64.rpm
# Upstream's checksum list, used in the prep section to verify Source0.
Source1:        https://github.com/storytold/effectcraft/releases/download/v%{version}/SHA256SUMS.txt

# The GUI stack (winit/xkbcommon) is dlopen()ed at runtime, so rpm's
# automatic ELF dependency detection does not see it. Upstream's own RPM
# requires these explicitly, so we do the same.
Requires:       libxkbcommon
Requires:       (vulkan-loader or mesa-libEGL)
Requires:       alsa-lib

# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64

%description
EffectCraft is an open-source motion graphics and visual effects compositor: layers with keyframes and a graph editor, masks and shapes, text animators, expressions, 3D cameras and lights, over 300 effects and a render queue, with GPU compositing.

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
install -Dm755 payload/usr/bin/effectcraft %{buildroot}%{_bindir}/effectcraft
install -Dm755 payload/usr/bin/effectcraft-cli %{buildroot}%{_bindir}/effectcraft-cli
install -Dm644 payload/usr/share/applications/ai.storyteller.effectcraft.desktop %{buildroot}%{_datadir}/applications/ai.storyteller.effectcraft.desktop
install -Dm644 payload/usr/share/doc/effectcraft/LICENSE-APACHE %{buildroot}%{_licensedir}/effectcraft/LICENSE-APACHE
install -Dm644 payload/usr/share/doc/effectcraft/LICENSE-MIT %{buildroot}%{_licensedir}/effectcraft/LICENSE-MIT
install -Dm644 payload/usr/share/doc/effectcraft/README.md %{buildroot}%{_docdir}/effectcraft/README.md
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/ai.storyteller.effectcraft.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.storyteller.effectcraft.png
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/ai.storyteller.effectcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.storyteller.effectcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/16x16/apps/ai.storyteller.effectcraft.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/ai.storyteller.effectcraft.png
install -Dm644 payload/usr/share/icons/hicolor/16x16/apps/ai.storyteller.effectcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/ai.storyteller.effectcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/24x24/apps/ai.storyteller.effectcraft.png %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/ai.storyteller.effectcraft.png
install -Dm644 payload/usr/share/icons/hicolor/24x24/apps/ai.storyteller.effectcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/ai.storyteller.effectcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/256x256/apps/ai.storyteller.effectcraft.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.storyteller.effectcraft.png
install -Dm644 payload/usr/share/icons/hicolor/256x256/apps/ai.storyteller.effectcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.storyteller.effectcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/ai.storyteller.effectcraft.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.storyteller.effectcraft.png
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/ai.storyteller.effectcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.storyteller.effectcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/48x48/apps/ai.storyteller.effectcraft.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/ai.storyteller.effectcraft.png
install -Dm644 payload/usr/share/icons/hicolor/48x48/apps/ai.storyteller.effectcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/ai.storyteller.effectcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/ai.storyteller.effectcraft.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.storyteller.effectcraft.png
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/ai.storyteller.effectcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.storyteller.effectcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/ai.storyteller.effectcraft.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.storyteller.effectcraft.png
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/ai.storyteller.effectcraft.png.attribution %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.storyteller.effectcraft.png.attribution
install -Dm644 payload/usr/share/icons/hicolor/scalable/apps/ai.storyteller.effectcraft.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.effectcraft.svg
install -Dm644 payload/usr/share/icons/hicolor/scalable/apps/ai.storyteller.effectcraft.svg.attribution %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.effectcraft.svg.attribution
install -Dm644 payload/usr/share/metainfo/ai.storyteller.effectcraft.metainfo.xml %{buildroot}%{_datadir}/metainfo/ai.storyteller.effectcraft.metainfo.xml
install -Dm644 payload/usr/share/mime/packages/ai.storyteller.effectcraft.xml %{buildroot}%{_datadir}/mime/packages/ai.storyteller.effectcraft.xml

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
%license %{_licensedir}/effectcraft/LICENSE-APACHE
%license %{_licensedir}/effectcraft/LICENSE-MIT
%doc %{_docdir}/effectcraft/README.md
%{_bindir}/effectcraft
%{_bindir}/effectcraft-cli
%{_datadir}/applications/ai.storyteller.effectcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.effectcraft.png
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.effectcraft.png.attribution
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.effectcraft.svg
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.effectcraft.svg.attribution
%{_datadir}/metainfo/ai.storyteller.effectcraft.metainfo.xml
%{_datadir}/mime/packages/ai.storyteller.effectcraft.xml

%changelog
* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.17.0-1
- update to 0.17.0

* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.16.0-1
- initial COPR package (rebundle of the upstream RPM)
