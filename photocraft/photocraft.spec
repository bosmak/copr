%global debug_package %{nil}
# Upstream ships prebuilt, already-stripped binaries. Re-running strip on
# them would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binaries bit-identical.
%global __strip /bin/true

Name:           photocraft
Version:        0.17.0
Release:        1%{?dist}
Summary:        Open-source image editor with familiar, professional tools
License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/photocraft
# Upstream publishes a prebuilt RPM for Linux. We rebundle its payload:
# the very same binaries and desktop integration, repacked with Fedora's
# directory layout (licenses under /usr/share/licenses, docs under
# /usr/share/doc) so the app can be installed straight from this project.
Source0:        https://github.com/storytold/photocraft/releases/download/v%{version}/photocraft-%{version}-linux-x86_64.rpm
# Upstream's checksum list, used in the prep section to verify Source0.
Source1:        https://github.com/storytold/photocraft/releases/download/v%{version}/SHA256SUMS.txt

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
PhotoCraft is an open-source, native image editor with the familiar menus, shortcuts, panels and tools professionals expect: layers, masks, adjustment layers, layer styles, type and brushes.

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
install -Dm755 payload/usr/bin/photocraft %{buildroot}%{_bindir}/photocraft
install -Dm755 payload/usr/bin/photocraft-cli %{buildroot}%{_bindir}/photocraft-cli
install -Dm644 payload/usr/share/applications/ai.storyteller.photocraft.desktop %{buildroot}%{_datadir}/applications/ai.storyteller.photocraft.desktop
install -Dm644 payload/usr/share/bash-completion/completions/photocraft-cli %{buildroot}%{_datadir}/bash-completion/completions/photocraft-cli
install -Dm644 payload/usr/share/doc/photocraft/ATTRIBUTION.md %{buildroot}%{_docdir}/photocraft/ATTRIBUTION.md
install -Dm644 payload/usr/share/doc/photocraft/LICENSE-APACHE %{buildroot}%{_licensedir}/photocraft/LICENSE-APACHE
install -Dm644 payload/usr/share/doc/photocraft/LICENSE-MIT %{buildroot}%{_licensedir}/photocraft/LICENSE-MIT
install -Dm644 payload/usr/share/doc/photocraft/NOTICE %{buildroot}%{_licensedir}/photocraft/NOTICE
install -Dm644 payload/usr/share/doc/photocraft/OFL-biz-ud-mincho.txt %{buildroot}%{_licensedir}/photocraft/OFL-biz-ud-mincho.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-biz-ud-pgothic.txt %{buildroot}%{_licensedir}/photocraft/OFL-biz-ud-pgothic.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-lxgw-wenkai-lite.txt %{buildroot}%{_licensedir}/photocraft/OFL-lxgw-wenkai-lite.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-nanum-gothic.txt %{buildroot}%{_licensedir}/photocraft/OFL-nanum-gothic.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-noto-sans-arabic.txt %{buildroot}%{_licensedir}/photocraft/OFL-noto-sans-arabic.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-noto-sans-cjk-sc.txt %{buildroot}%{_licensedir}/photocraft/OFL-noto-sans-cjk-sc.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-noto-sans-devanagari.txt %{buildroot}%{_licensedir}/photocraft/OFL-noto-sans-devanagari.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-noto-sans-georgian.txt %{buildroot}%{_licensedir}/photocraft/OFL-noto-sans-georgian.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-noto-sans-hebrew.txt %{buildroot}%{_licensedir}/photocraft/OFL-noto-sans-hebrew.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-noto-sans-symbols-2.txt %{buildroot}%{_licensedir}/photocraft/OFL-noto-sans-symbols-2.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-noto-sans-symbols.txt %{buildroot}%{_licensedir}/photocraft/OFL-noto-sans-symbols.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-noto-sans-thai.txt %{buildroot}%{_licensedir}/photocraft/OFL-noto-sans-thai.txt
install -Dm644 payload/usr/share/doc/photocraft/OFL-shippori-mincho.txt %{buildroot}%{_licensedir}/photocraft/OFL-shippori-mincho.txt
install -Dm644 payload/usr/share/doc/photocraft/README.md %{buildroot}%{_docdir}/photocraft/README.md
install -Dm644 payload/usr/share/fish/vendor_completions.d/photocraft-cli.fish %{buildroot}%{_datadir}/fish/vendor_completions.d/photocraft-cli.fish
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/ai.storyteller.photocraft.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.storyteller.photocraft.png
install -Dm644 payload/usr/share/icons/hicolor/16x16/apps/ai.storyteller.photocraft.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/ai.storyteller.photocraft.png
install -Dm644 payload/usr/share/icons/hicolor/24x24/apps/ai.storyteller.photocraft.png %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/ai.storyteller.photocraft.png
install -Dm644 payload/usr/share/icons/hicolor/256x256/apps/ai.storyteller.photocraft.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.storyteller.photocraft.png
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/ai.storyteller.photocraft.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.storyteller.photocraft.png
install -Dm644 payload/usr/share/icons/hicolor/48x48/apps/ai.storyteller.photocraft.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/ai.storyteller.photocraft.png
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/ai.storyteller.photocraft.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.storyteller.photocraft.png
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/ai.storyteller.photocraft.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.storyteller.photocraft.png
install -Dm644 payload/usr/share/icons/hicolor/scalable/apps/ai.storyteller.photocraft.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.photocraft.svg
install -Dm644 payload/usr/share/man/man1/photocraft-cli-batch.1 %{buildroot}%{_mandir}/man1/photocraft-cli-batch.1
install -Dm644 payload/usr/share/man/man1/photocraft-cli-commands.1 %{buildroot}%{_mandir}/man1/photocraft-cli-commands.1
install -Dm644 payload/usr/share/man/man1/photocraft-cli-convert.1 %{buildroot}%{_mandir}/man1/photocraft-cli-convert.1
install -Dm644 payload/usr/share/man/man1/photocraft-cli-droplet.1 %{buildroot}%{_mandir}/man1/photocraft-cli-droplet.1
install -Dm644 payload/usr/share/man/man1/photocraft-cli-info.1 %{buildroot}%{_mandir}/man1/photocraft-cli-info.1
install -Dm644 payload/usr/share/man/man1/photocraft-cli-mcp.1 %{buildroot}%{_mandir}/man1/photocraft-cli-mcp.1
install -Dm644 payload/usr/share/man/man1/photocraft-cli-run.1 %{buildroot}%{_mandir}/man1/photocraft-cli-run.1
install -Dm644 payload/usr/share/man/man1/photocraft-cli-serve.1 %{buildroot}%{_mandir}/man1/photocraft-cli-serve.1
install -Dm644 payload/usr/share/man/man1/photocraft-cli.1 %{buildroot}%{_mandir}/man1/photocraft-cli.1
install -Dm644 payload/usr/share/metainfo/ai.storyteller.photocraft.metainfo.xml %{buildroot}%{_datadir}/metainfo/ai.storyteller.photocraft.metainfo.xml
install -Dm644 payload/usr/share/mime/packages/ai.storyteller.photocraft.xml %{buildroot}%{_datadir}/mime/packages/ai.storyteller.photocraft.xml
install -Dm644 payload/usr/share/zsh/site-functions/_photocraft-cli %{buildroot}%{_datadir}/zsh/site-functions/_photocraft-cli

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
%license %{_licensedir}/photocraft/LICENSE-APACHE
%license %{_licensedir}/photocraft/LICENSE-MIT
%license %{_licensedir}/photocraft/NOTICE
%license %{_licensedir}/photocraft/OFL-*
%doc %{_docdir}/photocraft/ATTRIBUTION.md
%doc %{_docdir}/photocraft/README.md
%{_bindir}/photocraft
%{_bindir}/photocraft-cli
%{_datadir}/applications/ai.storyteller.photocraft.desktop
%{_datadir}/bash-completion/completions/photocraft-cli
%{_datadir}/fish/vendor_completions.d/photocraft-cli.fish
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.photocraft.png
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.photocraft.svg
%{_mandir}/man1/photocraft-cli-batch.1*
%{_mandir}/man1/photocraft-cli-commands.1*
%{_mandir}/man1/photocraft-cli-convert.1*
%{_mandir}/man1/photocraft-cli-droplet.1*
%{_mandir}/man1/photocraft-cli-info.1*
%{_mandir}/man1/photocraft-cli-mcp.1*
%{_mandir}/man1/photocraft-cli-run.1*
%{_mandir}/man1/photocraft-cli-serve.1*
%{_mandir}/man1/photocraft-cli.1*
%{_datadir}/metainfo/ai.storyteller.photocraft.metainfo.xml
%{_datadir}/mime/packages/ai.storyteller.photocraft.xml
%{_datadir}/zsh/site-functions/_photocraft-cli

%changelog
* Wed Oct 28 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 0.17.0-1
- update to 0.17.0

* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.16.0-1
- update to 0.16.0

* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.15.1-1
- initial COPR package (rebundle of the upstream RPM)
