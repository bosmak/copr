%global debug_package %{nil}
# Upstream ships a prebuilt, already-stripped binary. Re-running strip
# on it would mutate the ELF section metadata and diverge from
# upstream's released bytes; disabling it keeps the shipped binary as
# it was built (the runpath of it is fixed in the install section, but
# nothing else is touched).
%global __strip /bin/true

Name:           orca-slicer
Version:        2.5.0
Release:        1%{?dist}
Summary:        Advanced 3D printing slicer with improved compatibility
License:        AGPL-3.0-only
URL:            https://github.com/OrcaSlicer/OrcaSlicer
# Upstream publishes no RPM for Linux, only an AppImage. It is unpacked
# at build time and repacked with Fedora's directory layout, so the
# application is installed as a normal package instead of a self
# mounting blob.
#
# The name of the asset has changed over time (the "Ubuntu2404" and the
# "AppImage" parts appeared in 2.2.0 and 2.3.1), so it may have to be
# fixed here when upstream renames it again.
Source0:        https://github.com/OrcaSlicer/OrcaSlicer/releases/download/v%{version}/OrcaSlicer_Linux_AppImage_Ubuntu2404_V%{version}.AppImage
# The license and the AppStream metadata of the application. They are
# not in the AppImage, so they are pulled from the tag of the release.
Source1:        https://raw.githubusercontent.com/OrcaSlicer/OrcaSlicer/v%{version}/LICENSE.txt
Source2:        https://raw.githubusercontent.com/OrcaSlicer/OrcaSlicer/v%{version}/scripts/flatpak/com.orcaslicer.OrcaSlicer.metainfo.xml
# The launcher and the desktop integration of the package. They are not
# part of upstream's release, so they are vendored in this repository.
Source3:        orca-slicer-launcher
Source4:        com.orcaslicer.OrcaSlicer.desktop
Source5:        com.orcaslicer.OrcaSlicer.xml

# The runpath of the binary is fixed with patchelf in the install
# section.
BuildRequires:  patchelf

# The 3D view needs a GL driver. The software renderer of Mesa is
# enough when there is no hardware acceleration.
Recommends:     mesa-dri-drivers
# The web view of the application plays videos with GStreamer.
Recommends:     gstreamer1-plugins-good
# update-mime-database is used by the post-install scriptlet.
Requires(post): shared-mime-info
Requires(postun): shared-mime-info

# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64

%description
OrcaSlicer is a 3D printing slicer: it turns the models of a printer
into the G-code that the printer runs. It is a fork of PrusaSlicer with
improved supports, better compatibility with the printers of other
brands and a few extra features.

The package ships the desktop application, its command line interface
(the same binary, driven by the options), the desktop entry, the icon
and the AppStream metadata.

This is built from the AppImage published by upstream: the binary and
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
# Nothing to build — we ship upstream's prebuilt binary verbatim.

%install
# The application looks for its data in the "resources" directory that
# sits next to the "bin" directory holding the binary. The layout of the
# AppImage is kept under the private directory of the package, so the
# application finds its data wherever it is installed and nothing else
# can be confused by it.
install -Dm755 squashfs-root/bin/orca-slicer %{buildroot}%{_libexecdir}/orca-slicer/bin/orca-slicer
cp -a squashfs-root/resources %{buildroot}%{_libexecdir}/orca-slicer/resources

# The runpath of the binary points to the build machine of upstream
# (a directory that does not exist anywhere else), so it is useless and
# rpm refuses to package a binary with it.
patchelf --remove-rpath %{buildroot}%{_libexecdir}/orca-slicer/bin/orca-slicer

# The launcher runs the binary of the private directory. It is rewritten
# here so the path of the binary is not hardcoded in the repository.
sed 's|^exec .*|exec %{_libexecdir}/orca-slicer/bin/orca-slicer "$@"|' \
    %{SOURCE3} \
    | install -Dm755 /dev/stdin %{buildroot}%{_bindir}/orca-slicer

install -Dm644 %{SOURCE4} %{buildroot}%{_datadir}/applications/com.orcaslicer.OrcaSlicer.desktop
install -Dm644 %{SOURCE5} %{buildroot}%{_datadir}/mime/packages/com.orcaslicer.OrcaSlicer.xml
install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/metainfo/com.orcaslicer.OrcaSlicer.metainfo.xml

# The icon of the application is the one of the AppImage: the 192px
# version of it.
install -Dm644 squashfs-root/resources/images/OrcaSlicer_192px.png %{buildroot}%{_datadir}/icons/hicolor/192x192/apps/OrcaSlicer.png

install -Dm644 %{SOURCE1} %{buildroot}%{_licensedir}/orca-slicer/LICENSE.txt

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
%license %{_licensedir}/orca-slicer/LICENSE.txt
%{_bindir}/orca-slicer
%{_libexecdir}/orca-slicer/bin/orca-slicer
%{_libexecdir}/orca-slicer/resources
%{_datadir}/applications/com.orcaslicer.OrcaSlicer.desktop
%{_datadir}/icons/hicolor/192x192/apps/OrcaSlicer.png
%{_datadir}/metainfo/com.orcaslicer.OrcaSlicer.metainfo.xml
%{_datadir}/mime/packages/com.orcaslicer.OrcaSlicer.xml

%changelog
* Sat Nov 07 2026 github-actions[bot] <github-actions[bot]@users.noreply.github.com> - 2.5.0-1
- update to 2.5.0

* Fri Nov 06 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 2.4.2-1
- initial COPR package (built from the upstream AppImage)
- sha256 of the AppImage:
  d12fb8c8eac1aecd2dfb6377acd48f994f8fa439ed5292fa532dd82880f029fd
