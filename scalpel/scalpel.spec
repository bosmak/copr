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
#
# The FFI library of the application also ships the scripts that build
# it, with the shebang of the node of the system. The application never
# runs them with the node of the system, so they must not become a
# dependency of the package either.
%global __requires_exclude ^(/usr/bin/node|(libffmpeg|libEGL|libGLESv2|libvk_swiftshader|libvulkan)([.]so.*)?)$
%global __provides_exclude ^(libffmpeg|libEGL|libGLESv2|libvk_swiftshader|libvulkan)([.]so.*)?$

# The shebang of the scripts above is rewritten by the build system
# when the node of the system is installed, which makes the payload
# depend on the build environment. They are never run, so the bytes of
# upstream are shipped as they are.
%global __brp_mangle_shebangs %{nil}

Name:           scalpel
Version:        1.0.6
Release:        1%{?dist}
Summary:        Overlay to edit the loot filter of Path of Exile and price check items
License:        AGPL-3.0-only
URL:            https://github.com/scalpelpoe/scalpel
# Upstream publishes the application as an AppImage only. It is
# unpacked at build time and repacked with Fedora's directory layout,
# so the application is installed as a normal package instead of a
# self-mounting blob.
Source0:        https://github.com/scalpelpoe/scalpel/releases/download/v%{version}/Scalpel.AppImage
# The license of the application and the notices of the third-party
# software it uses are not in the AppImage, so they are pulled from the
# tag of the release.
Source1:        https://raw.githubusercontent.com/scalpelpoe/scalpel/v%{version}/LICENSE
Source2:        https://raw.githubusercontent.com/scalpelpoe/scalpel/v%{version}/THIRD-PARTY-NOTICES.md
# The launcher and the desktop entry of the package. They are not part
# of upstream's release, so they are vendored in this repository.
Source3:        scalpel-launcher
Source4:        scalpel.desktop

# The runtime of the application is the one of Electron: the build
# needs the libraries of the graphical stack of the system, so the
# automatic dependency generator can resolve them.
BuildRequires:  alsa-lib
BuildRequires:  at-spi2-atk
BuildRequires:  cups-libs
BuildRequires:  dbus-libs
BuildRequires:  gtk3
BuildRequires:  mesa-libgbm
BuildRequires:  nspr
BuildRequires:  nss
BuildRequires:  pango

# The global hotkeys of the application are handled by uiohook, which
# needs the X11 test extension and the X11 toolkit. The graphical stack
# of the system does not pull them in.
Requires:       libXt
Requires:       libXtst
# The notifications of the application are sent through libnotify.
Requires:       libnotify

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
Scalpel is an overlay for Path of Exile: it edits the loot filter of
the game while it runs, price checks the items on the screen, audits
the economy of the league and generates the regex of the item filters.

It is an Electron application: it runs on the desktop, over the game,
and it does not need a browser.

This is built from the AppImage published by upstream: the runtime and
the data of the application are the very same ones the AppImage ships.

%prep
# Upstream publishes no checksum list for its releases, so the AppImage
# is fetched over TLS from the official release page. Its digest is
# recorded in the changelog.

# Unpack the AppImage. The runtime extracts its own payload, so no FUSE
# is needed in the build root.
chmod +x %{SOURCE0}
%{SOURCE0} --appimage-extract

%build
# Nothing to build — we ship upstream's prebuilt runtime verbatim.

%install
# The application looks for its data in the "resources" directory that
# sits next to the binary, so the layout of the AppImage is kept under
# the private directory of the package: the runtime finds its data
# wherever it is installed.
install -d %{buildroot}%{_libexecdir}/scalpel
cp -a squashfs-root/scalpel \
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
      %{buildroot}%{_libexecdir}/scalpel/

# The runtime of the AppImage creates the directories of the payload
# with restrictive permissions, so the users of the package cannot read
# the data of the application.
chmod -R u+rwX,go+rX %{buildroot}%{_libexecdir}/scalpel

# The FFI library ships a build of its native module for the musl libc.
# The loader of the library picks the one of the libc of the system, so
# the build for musl is never used here — and it needs a library that
# Fedora does not ship.
rm -rf %{buildroot}%{_libexecdir}/scalpel/resources/app.asar.unpacked/node_modules/@koromix/koffi-linux-x64/musl_x64

# The helper of the Chromium sandbox. It is only used when the
# unprivileged user namespaces are not available, but Chromium refuses
# to start when it finds it without the setuid bit.
install -Dm755 squashfs-root/chrome-sandbox \
    %{buildroot}%{_libexecdir}/scalpel/chrome-sandbox

# The launcher runs the runtime of the private directory. It is
# rewritten here so the path of the runtime is not hardcoded in the
# repository.
sed 's|^exec @libexecdir@|exec %{_libexecdir}|' \
    %{SOURCE3} \
    | install -Dm755 /dev/stdin %{buildroot}%{_bindir}/scalpel

install -Dm644 %{SOURCE4} %{buildroot}%{_datadir}/applications/scalpel.desktop

# The icon of the application is the one of the AppImage: the 256px
# version of it.
install -Dm644 squashfs-root/usr/share/icons/hicolor/256x256/apps/scalpel.png \
    %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/scalpel.png

install -Dm644 %{SOURCE1} %{buildroot}%{_licensedir}/scalpel/LICENSE
install -Dm644 %{SOURCE2} %{buildroot}%{_docdir}/scalpel/THIRD-PARTY-NOTICES.md
install -Dm644 squashfs-root/LICENSE.electron.txt \
    %{buildroot}%{_licensedir}/scalpel/LICENSE.electron.txt
install -Dm644 squashfs-root/LICENSES.chromium.html \
    %{buildroot}%{_licensedir}/scalpel/LICENSES.chromium.html

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
%license %{_licensedir}/scalpel/LICENSE
%license %{_licensedir}/scalpel/LICENSE.electron.txt
%license %{_licensedir}/scalpel/LICENSES.chromium.html
%doc %{_docdir}/scalpel/THIRD-PARTY-NOTICES.md
%{_bindir}/scalpel
%{_libexecdir}/scalpel/scalpel
%attr(4755,root,root) %{_libexecdir}/scalpel/chrome-sandbox
%{_libexecdir}/scalpel/chrome_100_percent.pak
%{_libexecdir}/scalpel/chrome_200_percent.pak
%{_libexecdir}/scalpel/chrome_crashpad_handler
%{_libexecdir}/scalpel/icudtl.dat
%{_libexecdir}/scalpel/libEGL.so
%{_libexecdir}/scalpel/libffmpeg.so
%{_libexecdir}/scalpel/libGLESv2.so
%{_libexecdir}/scalpel/libvk_swiftshader.so
%{_libexecdir}/scalpel/libvulkan.so.1
%{_libexecdir}/scalpel/locales
%{_libexecdir}/scalpel/resources
%{_libexecdir}/scalpel/resources.pak
%{_libexecdir}/scalpel/snapshot_blob.bin
%{_libexecdir}/scalpel/v8_context_snapshot.bin
%{_libexecdir}/scalpel/vk_swiftshader_icd.json
%{_datadir}/applications/scalpel.desktop
%{_datadir}/icons/hicolor/256x256/apps/scalpel.png

%changelog
* Thu Nov 19 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 1.0.6-1
- initial COPR package (built from the upstream AppImage)
- sha256 of the AppImage:
  61f0af582af039609899c5c612b6a5785fd0368384b19aa0ef4bed8eca503d54
