%global debug_package %{nil}
# Upstream ships prebuilt, already-stripped binaries. Re-running strip on
# them would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binaries bit-identical.
%global __strip /bin/true

Name:           figcraft
Version:        0.12.1
Release:        1%{?dist}
Summary:        Open-source interface design and prototyping tool
License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/figcraft
# Upstream publishes a prebuilt RPM for Linux. We rebundle its payload:
# the very same binaries and desktop integration, repacked with Fedora's
# directory layout (licenses under /usr/share/licenses, docs under
# /usr/share/doc) so the app can be installed straight from this project.
Source0:        https://github.com/storytold/figcraft/releases/download/v%{version}/figcraft-%{version}-linux-x86_64.rpm
# Upstream's checksum list, used in the prep section to verify Source0.
Source1:        https://github.com/storytold/figcraft/releases/download/v%{version}/SHA256SUMS.txt

# The GUI stack (winit/xkbcommon) is dlopen()ed at runtime, so rpm's
# automatic ELF dependency detection does not see it. Upstream's own RPM
# requires these explicitly, so we do the same.
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
FigCraft is an open-source, native interface design and prototyping tool. Lay out screens on an infinite canvas with frames, auto layout and constraints, build reusable components and variants, and link screens into clickable prototypes.

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
install -Dm755 payload/usr/bin/figcraft %{buildroot}%{_bindir}/figcraft
install -Dm755 payload/usr/bin/figcraft-cli %{buildroot}%{_bindir}/figcraft-cli
install -Dm644 payload/usr/share/applications/ai.storyteller.figcraft.desktop %{buildroot}%{_datadir}/applications/ai.storyteller.figcraft.desktop
install -Dm644 payload/usr/share/doc/figcraft/LICENSE-APACHE %{buildroot}%{_licensedir}/figcraft/LICENSE-APACHE
install -Dm644 payload/usr/share/doc/figcraft/LICENSE-MIT %{buildroot}%{_licensedir}/figcraft/LICENSE-MIT
install -Dm644 payload/usr/share/doc/figcraft/NOTICE %{buildroot}%{_licensedir}/figcraft/NOTICE
install -Dm644 payload/usr/share/doc/figcraft/OFL-biz-ud-mincho.txt %{buildroot}%{_licensedir}/figcraft/OFL-biz-ud-mincho.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-biz-ud-pgothic.txt %{buildroot}%{_licensedir}/figcraft/OFL-biz-ud-pgothic.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-caladea.txt %{buildroot}%{_licensedir}/figcraft/OFL-caladea.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-carlito.txt %{buildroot}%{_licensedir}/figcraft/OFL-carlito.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-inter.txt %{buildroot}%{_licensedir}/figcraft/OFL-inter.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-lato.txt %{buildroot}%{_licensedir}/figcraft/OFL-lato.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-liberation-mono.txt %{buildroot}%{_licensedir}/figcraft/OFL-liberation-mono.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-liberation-sans.txt %{buildroot}%{_licensedir}/figcraft/OFL-liberation-sans.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-liberation-serif.txt %{buildroot}%{_licensedir}/figcraft/OFL-liberation-serif.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-lxgw-wenkai-lite.txt %{buildroot}%{_licensedir}/figcraft/OFL-lxgw-wenkai-lite.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-merriweather.txt %{buildroot}%{_licensedir}/figcraft/OFL-merriweather.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-montserrat.txt %{buildroot}%{_licensedir}/figcraft/OFL-montserrat.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-nanum-gothic.txt %{buildroot}%{_licensedir}/figcraft/OFL-nanum-gothic.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-noto-sans-arabic.txt %{buildroot}%{_licensedir}/figcraft/OFL-noto-sans-arabic.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-noto-sans-cjk-sc.txt %{buildroot}%{_licensedir}/figcraft/OFL-noto-sans-cjk-sc.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-noto-sans-devanagari.txt %{buildroot}%{_licensedir}/figcraft/OFL-noto-sans-devanagari.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-noto-sans-georgian.txt %{buildroot}%{_licensedir}/figcraft/OFL-noto-sans-georgian.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-noto-sans-hebrew.txt %{buildroot}%{_licensedir}/figcraft/OFL-noto-sans-hebrew.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-noto-sans-symbols-2.txt %{buildroot}%{_licensedir}/figcraft/OFL-noto-sans-symbols-2.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-noto-sans-symbols.txt %{buildroot}%{_licensedir}/figcraft/OFL-noto-sans-symbols.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-noto-sans-thai.txt %{buildroot}%{_licensedir}/figcraft/OFL-noto-sans-thai.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-nunito-sans.txt %{buildroot}%{_licensedir}/figcraft/OFL-nunito-sans.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-open-sans.txt %{buildroot}%{_licensedir}/figcraft/OFL-open-sans.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-playfair-display.txt %{buildroot}%{_licensedir}/figcraft/OFL-playfair-display.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-poppins.txt %{buildroot}%{_licensedir}/figcraft/OFL-poppins.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-roboto.txt %{buildroot}%{_licensedir}/figcraft/OFL-roboto.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-shippori-mincho.txt %{buildroot}%{_licensedir}/figcraft/OFL-shippori-mincho.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-source-sans-3.txt %{buildroot}%{_licensedir}/figcraft/OFL-source-sans-3.txt
install -Dm644 payload/usr/share/doc/figcraft/OFL-source-serif-4.txt %{buildroot}%{_licensedir}/figcraft/OFL-source-serif-4.txt
install -Dm644 payload/usr/share/doc/figcraft/README.md %{buildroot}%{_docdir}/figcraft/README.md
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/ai.storyteller.figcraft.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.storyteller.figcraft.png
install -Dm644 payload/usr/share/icons/hicolor/16x16/apps/ai.storyteller.figcraft.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/ai.storyteller.figcraft.png
install -Dm644 payload/usr/share/icons/hicolor/256x256/apps/ai.storyteller.figcraft.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.storyteller.figcraft.png
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/ai.storyteller.figcraft.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.storyteller.figcraft.png
install -Dm644 payload/usr/share/icons/hicolor/48x48/apps/ai.storyteller.figcraft.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/ai.storyteller.figcraft.png
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/ai.storyteller.figcraft.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.storyteller.figcraft.png
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/ai.storyteller.figcraft.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.storyteller.figcraft.png
install -Dm644 payload/usr/share/icons/hicolor/scalable/apps/ai.storyteller.figcraft.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.figcraft.svg
install -Dm644 payload/usr/share/metainfo/ai.storyteller.figcraft.metainfo.xml %{buildroot}%{_datadir}/metainfo/ai.storyteller.figcraft.metainfo.xml
install -Dm644 payload/usr/share/mime/packages/ai.storyteller.figcraft.xml %{buildroot}%{_datadir}/mime/packages/ai.storyteller.figcraft.xml

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
%license %{_licensedir}/figcraft/LICENSE-APACHE
%license %{_licensedir}/figcraft/LICENSE-MIT
%license %{_licensedir}/figcraft/NOTICE
%license %{_licensedir}/figcraft/OFL-*
%doc %{_docdir}/figcraft/README.md
%{_bindir}/figcraft
%{_bindir}/figcraft-cli
%{_datadir}/applications/ai.storyteller.figcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.figcraft.png
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.figcraft.svg
%{_datadir}/metainfo/ai.storyteller.figcraft.metainfo.xml
%{_datadir}/mime/packages/ai.storyteller.figcraft.xml

%changelog
* Wed Oct 28 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 0.12.1-1
- update to 0.12.1

* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.11.2-1
- update to 0.11.2

* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.10.0-1
- initial COPR package (rebundle of the upstream RPM)
