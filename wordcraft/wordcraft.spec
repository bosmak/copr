%global debug_package %{nil}
# Upstream ships prebuilt, already-stripped binaries. Re-running strip on
# them would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binaries bit-identical.
%global __strip /bin/true

Name:           wordcraft
Version:        0.13.2
Release:        1%{?dist}
Summary:        Open-source word processor that works the way Word users expect
License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/wordcraft
# Upstream publishes a prebuilt RPM for Linux. We rebundle its payload:
# the very same binaries and desktop integration, repacked with Fedora's
# directory layout (licenses under /usr/share/licenses, docs under
# /usr/share/doc) so the app can be installed straight from this project.
Source0:        https://github.com/storytold/wordcraft/releases/download/v%{version}/wordcraft-%{version}-linux-x86_64.rpm
# Upstream's checksum list, used in the prep section to verify Source0.
Source1:        https://github.com/storytold/wordcraft/releases/download/v%{version}/SHA256SUMS.txt

# The GUI stack (winit/xkbcommon) is dlopen()ed at runtime, so rpm's
# automatic ELF dependency detection does not see it. Upstream's own RPM
# requires these explicitly, so we do the same.
Requires:       libxkbcommon
Requires:       (vulkan-loader or mesa-libEGL)

# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64

%description
WordCraft is a fast, open-source word processor with a familiar ribbon: styles, tables, track changes, references, mail merge, and .docx, PDF, ODT, RTF, HTML and Markdown files. It can be driven by AI agents over MCP.

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
install -Dm755 payload/usr/bin/wordcraft %{buildroot}%{_bindir}/wordcraft
install -Dm755 payload/usr/bin/wordcraft-cli %{buildroot}%{_bindir}/wordcraft-cli
install -Dm644 payload/usr/share/applications/ai.storyteller.wordcraft.desktop %{buildroot}%{_datadir}/applications/ai.storyteller.wordcraft.desktop
install -Dm644 payload/usr/share/doc/wordcraft/ATTRIBUTION.md %{buildroot}%{_docdir}/wordcraft/ATTRIBUTION.md
install -Dm644 payload/usr/share/doc/wordcraft/LICENSE-APACHE %{buildroot}%{_licensedir}/wordcraft/LICENSE-APACHE
install -Dm644 payload/usr/share/doc/wordcraft/LICENSE-MIT %{buildroot}%{_licensedir}/wordcraft/LICENSE-MIT
install -Dm644 payload/usr/share/doc/wordcraft/NOTICE %{buildroot}%{_licensedir}/wordcraft/NOTICE
install -Dm644 payload/usr/share/doc/wordcraft/OFL-biz-ud-mincho.txt %{buildroot}%{_licensedir}/wordcraft/OFL-biz-ud-mincho.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-biz-ud-pgothic.txt %{buildroot}%{_licensedir}/wordcraft/OFL-biz-ud-pgothic.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-lxgw-wenkai-lite.txt %{buildroot}%{_licensedir}/wordcraft/OFL-lxgw-wenkai-lite.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-nanum-gothic.txt %{buildroot}%{_licensedir}/wordcraft/OFL-nanum-gothic.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-noto-sans-arabic.txt %{buildroot}%{_licensedir}/wordcraft/OFL-noto-sans-arabic.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-noto-sans-cjk-sc.txt %{buildroot}%{_licensedir}/wordcraft/OFL-noto-sans-cjk-sc.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-noto-sans-devanagari.txt %{buildroot}%{_licensedir}/wordcraft/OFL-noto-sans-devanagari.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-noto-sans-georgian.txt %{buildroot}%{_licensedir}/wordcraft/OFL-noto-sans-georgian.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-noto-sans-hebrew.txt %{buildroot}%{_licensedir}/wordcraft/OFL-noto-sans-hebrew.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-noto-sans-symbols-2.txt %{buildroot}%{_licensedir}/wordcraft/OFL-noto-sans-symbols-2.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-noto-sans-symbols.txt %{buildroot}%{_licensedir}/wordcraft/OFL-noto-sans-symbols.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-noto-sans-thai.txt %{buildroot}%{_licensedir}/wordcraft/OFL-noto-sans-thai.txt
install -Dm644 payload/usr/share/doc/wordcraft/OFL-shippori-mincho.txt %{buildroot}%{_licensedir}/wordcraft/OFL-shippori-mincho.txt
install -Dm644 payload/usr/share/doc/wordcraft/README.md %{buildroot}%{_docdir}/wordcraft/README.md
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/ai.storyteller.wordcraft.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.storyteller.wordcraft.png
install -Dm644 payload/usr/share/icons/hicolor/16x16/apps/ai.storyteller.wordcraft.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/ai.storyteller.wordcraft.png
install -Dm644 payload/usr/share/icons/hicolor/24x24/apps/ai.storyteller.wordcraft.png %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/ai.storyteller.wordcraft.png
install -Dm644 payload/usr/share/icons/hicolor/256x256/apps/ai.storyteller.wordcraft.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.storyteller.wordcraft.png
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/ai.storyteller.wordcraft.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.storyteller.wordcraft.png
install -Dm644 payload/usr/share/icons/hicolor/48x48/apps/ai.storyteller.wordcraft.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/ai.storyteller.wordcraft.png
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/ai.storyteller.wordcraft.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.storyteller.wordcraft.png
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/ai.storyteller.wordcraft.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.storyteller.wordcraft.png
install -Dm644 payload/usr/share/icons/hicolor/scalable/apps/ai.storyteller.wordcraft.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.wordcraft.svg
install -Dm644 payload/usr/share/metainfo/ai.storyteller.wordcraft.metainfo.xml %{buildroot}%{_datadir}/metainfo/ai.storyteller.wordcraft.metainfo.xml
install -Dm644 payload/usr/share/mime/packages/ai.storyteller.wordcraft.xml %{buildroot}%{_datadir}/mime/packages/ai.storyteller.wordcraft.xml

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
%license %{_licensedir}/wordcraft/LICENSE-APACHE
%license %{_licensedir}/wordcraft/LICENSE-MIT
%license %{_licensedir}/wordcraft/NOTICE
%license %{_licensedir}/wordcraft/OFL-*
%doc %{_docdir}/wordcraft/ATTRIBUTION.md
%doc %{_docdir}/wordcraft/README.md
%{_bindir}/wordcraft
%{_bindir}/wordcraft-cli
%{_datadir}/applications/ai.storyteller.wordcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.wordcraft.png
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.wordcraft.svg
%{_datadir}/metainfo/ai.storyteller.wordcraft.metainfo.xml
%{_datadir}/mime/packages/ai.storyteller.wordcraft.xml

%changelog
* Sat Oct 31 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 0.13.2-1
- update to 0.13.2

* Wed Oct 28 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 0.12.0-1
- update to 0.12.0

* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.11.0-1
- update to 0.11.0

* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.10.0-1
- initial COPR package (rebundle of the upstream RPM)
