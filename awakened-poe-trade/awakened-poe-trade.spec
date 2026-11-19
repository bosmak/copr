%global debug_package %{nil}
# Upstream ships a prebuilt, already-stripped binary: the AppImage
# bundles the Electron runtime of the application. Re-running strip on
# it would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binary as it was
# built.
%global __strip /bin/true

# The AppImage bundles its own copies of these libraries. They are
# shipped in the private directory of the package, so the automatic
# dependency generator must not turn them into requires that nothing
# provides. They are not provided either: libvulkan.so.1 is also
# provided by the mesa-vulkan-drivers of the system, and the private
# copy of it must not take the place of the one of the system.
%global __requires_exclude ^(libffmpeg|libEGL|libGLESv2|libvk_swiftshader|libvulkan)([.]so.*)?$
%global __provides_exclude ^(libffmpeg|libEGL|libGLESv2|libvk_swiftshader|libvulkan)([.]so.*)?$

Name:           awakened-poe-trade
Version:        3.30.102
Release:        1%{?dist}
Summary:        Search the prices of the items of Path of Exile
License:        MIT AND BSD-3-Clause
URL:            https://github.com/SnosMe/awakened-poe-trade
# Upstream publishes the application as an AppImage only. It is
# unpacked at build time and repacked with Fedora's directory layout,
# so the application is installed as a normal package instead of a
# self-mounting blob.
Source0:        https://github.com/SnosMe/awakened-poe-trade/releases/download/v%{version}/Awakened-PoE-Trade-%{version}.AppImage
# The license of the application is not in the AppImage, so it is
# pulled from the tag of the release.
Source1:        https://raw.githubusercontent.com/SnosMe/awakened-poe-trade/v%{version}/LICENSE
# The launcher and the desktop entry of the package. They are not part
# of upstream's release, so they are vendored in this repository.
Source2:        awakened-poe-trade-launcher
Source3:        awakened-poe-trade.desktop

# The application is a graphical one: it needs the GL driver of the
# system to render its window. The software renderer of Mesa is enough
# when there is no hardware acceleration.
Recommends:     mesa-dri-drivers
# The helpers that refresh the caches of the desktop entry and of the
# icons are used by the post-install scriptlet.
Requires(post): desktop-file-utils
Requires(post): gtk-update-icon-cache

# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64

%description
Awakened PoE Trade is a price checker for Path of Exile: it looks for
the prices of the items of the official trade API and of the community
ones, so the price of a drop can be known before picking it up.

It is an Electron application: it runs on the desktop, with its own
window, and it does not need a browser.

This is built from the AppImage published by upstream: the runtime and
the data of the application are the very same ones the AppImage ships.

%prep
# Upstream publishes no checksum list for its releases, so the AppImage
# is fetched over TLS from the official release page. Its digest is
# recorded in the changelog.

# Unpack the AppImage. The runtime extracts its own payload, so no
# FUSE is needed in the build root.
chmod +x %{SOURCE0}
%{SOURCE0} --appimage-extract

%build
# Nothing to build — we ship upstream's prebuilt runtime verbatim.

%install
# The application looks for its data in the "resources" directory that
# sits next to the binary, so the layout of the AppImage is kept under
# the private directory of the package: the runtime finds its data
# wherever it is installed.
install -d %{buildroot}%{_libexecdir}/awakened-poe-trade
cp -a squashfs-root/awakened-poe-trade \
      squashfs-root/chrome_100_percent.pak \
      squashfs-root/chrome_200_percent.pak \
      squashfs-root/chrome_crashpad_handler \
      squashfs-root/icudtl.dat \
      squashfs-root/libEGL.so \
      squashfs-root/libffmpeg.so \
      squashfs-root/libGLESv2.so \
      squashfs-root/libvk_swiftshader.so \
      squashfs-root/libvulkan.so.1 \
      squashfs-root/locales \
      squashfs-root/resources \
      squashfs-root/resources.pak \
      squashfs-root/snapshot_blob.bin \
      squashfs-root/v8_context_snapshot.bin \
      squashfs-root/vk_swiftshader_icd.json \
      %{buildroot}%{_libexecdir}/awakened-poe-trade/

# The helper of the Chromium sandbox. It is only used when the
# unprivileged user namespaces are not available, but Chromium refuses
# to start when it finds it without the setuid bit.
install -Dm755 squashfs-root/chrome-sandbox \
    %{buildroot}%{_libexecdir}/awakened-poe-trade/chrome-sandbox

# The launcher runs the runtime of the private directory. It is
# rewritten here so the path of the runtime is not hardcoded in the
# repository.
sed 's|^exec @libexecdir@|exec %{_libexecdir}|' \
    %{SOURCE2} \
    | install -Dm755 /dev/stdin %{buildroot}%{_bindir}/awakened-poe-trade

install -Dm644 %{SOURCE3} %{buildroot}%{_datadir}/applications/awakened-poe-trade.desktop

# The icons of the application are the ones of the AppImage.
for size in 16 24 32 48 64 128 256 512 1024; do
    install -Dm644 \
        squashfs-root/usr/share/icons/hicolor/${size}x${size}/apps/awakened-poe-trade.png \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/awakened-poe-trade.png
done

install -Dm644 %{SOURCE1} %{buildroot}%{_licensedir}/awakened-poe-trade/LICENSE
install -Dm644 squashfs-root/LICENSE.electron.txt \
    %{buildroot}%{_licensedir}/awakened-poe-trade/LICENSE.electron.txt
install -Dm644 squashfs-root/LICENSES.chromium.html \
    %{buildroot}%{_licensedir}/awakened-poe-trade/LICENSES.chromium.html

%post
# Refresh the desktop entry and the icon cache. Every helper is
# optional, so a missing one is simply skipped.
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
%license %{_licensedir}/awakened-poe-trade/LICENSE
%license %{_licensedir}/awakened-poe-trade/LICENSE.electron.txt
%license %{_licensedir}/awakened-poe-trade/LICENSES.chromium.html
%{_bindir}/awakened-poe-trade
%{_libexecdir}/awakened-poe-trade/awakened-poe-trade
%attr(4755,root,root) %{_libexecdir}/awakened-poe-trade/chrome-sandbox
%{_libexecdir}/awakened-poe-trade/chrome_100_percent.pak
%{_libexecdir}/awakened-poe-trade/chrome_200_percent.pak
%{_libexecdir}/awakened-poe-trade/chrome_crashpad_handler
%{_libexecdir}/awakened-poe-trade/icudtl.dat
%{_libexecdir}/awakened-poe-trade/libEGL.so
%{_libexecdir}/awakened-poe-trade/libffmpeg.so
%{_libexecdir}/awakened-poe-trade/libGLESv2.so
%{_libexecdir}/awakened-poe-trade/libvk_swiftshader.so
%{_libexecdir}/awakened-poe-trade/libvulkan.so.1
%{_libexecdir}/awakened-poe-trade/locales
%{_libexecdir}/awakened-poe-trade/resources
%{_libexecdir}/awakened-poe-trade/resources.pak
%{_libexecdir}/awakened-poe-trade/snapshot_blob.bin
%{_libexecdir}/awakened-poe-trade/v8_context_snapshot.bin
%{_libexecdir}/awakened-poe-trade/vk_swiftshader_icd.json
%{_datadir}/applications/awakened-poe-trade.desktop
%{_datadir}/icons/hicolor/16x16/apps/awakened-poe-trade.png
%{_datadir}/icons/hicolor/24x24/apps/awakened-poe-trade.png
%{_datadir}/icons/hicolor/32x32/apps/awakened-poe-trade.png
%{_datadir}/icons/hicolor/48x48/apps/awakened-poe-trade.png
%{_datadir}/icons/hicolor/64x64/apps/awakened-poe-trade.png
%{_datadir}/icons/hicolor/128x128/apps/awakened-poe-trade.png
%{_datadir}/icons/hicolor/256x256/apps/awakened-poe-trade.png
%{_datadir}/icons/hicolor/512x512/apps/awakened-poe-trade.png
%{_datadir}/icons/hicolor/1024x1024/apps/awakened-poe-trade.png

%changelog
* Thu Nov 19 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 3.30.102-1
- initial COPR package (built from the upstream AppImage)
- sha256 of the AppImage:
  87f8535aebaf16f1d7fa5bc549673cac077911eca5a77799043cd6916bbbcc63
