%global debug_package %{nil}
# Upstream ships prebuilt, already-stripped binaries. Re-running strip on
# them would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binaries bit-identical.
%global __strip /bin/true

Name:           solidcraft
Version:        0.22.1
Release:        1%{?dist}
Summary:        Open-source parametric 3D CAD application
License:        MIT OR Apache-2.0
URL:            https://solidcraft.io
# Upstream publishes a prebuilt RPM for Linux. We rebundle its payload:
# the very same binaries and desktop integration, repacked with Fedora's
# directory layout (licenses under /usr/share/licenses, docs under
# /usr/share/doc) so the app can be installed straight from this project.
Source0:        https://github.com/tangency-labs/solidcraft/releases/download/v%{version}/solidcraft-%{version}-linux-x86_64.rpm
# Upstream's checksum list, used in the prep section to verify Source0.
Source1:        https://github.com/tangency-labs/solidcraft/releases/download/v%{version}/SHA256SUMS.txt

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
# update-mime-database is used by the post-install scriptlet.
Requires(post): shared-mime-info
# The GPU drivers the renderer talks to; not needed to install the app.
Recommends:     mesa-vulkan-drivers
Recommends:     mesa-dri-drivers

# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64

%description
SolidCraft is an open-source parametric 3D CAD application written in Rust.
Sketch on a plane, constrain and dimension the sketch, turn profiles into
solids on a feature timeline, and change a parameter to watch the timeline
rebuild.

The package ships the desktop application (solidcraft), the headless command
line interface (solidcraft-cli) and its legacy alias (solvecraft-cli), plus
the desktop entry, the AppStream metadata and the .solidcraft MIME type.

This is a rebundle of the RPM published by upstream: the binaries are the
very same ones upstream ships.

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
install -Dm755 payload/usr/bin/solidcraft %{buildroot}%{_bindir}/solidcraft
install -Dm755 payload/usr/bin/solidcraft-cli %{buildroot}%{_bindir}/solidcraft-cli
install -Dm755 payload/usr/bin/solvecraft-cli %{buildroot}%{_bindir}/solvecraft-cli
install -Dm644 payload/usr/share/applications/ai.storyteller.solidcraft.desktop %{buildroot}%{_datadir}/applications/ai.storyteller.solidcraft.desktop
install -Dm644 payload/usr/share/doc/solidcraft/LICENSE-APACHE %{buildroot}%{_licensedir}/solidcraft/LICENSE-APACHE
install -Dm644 payload/usr/share/doc/solidcraft/LICENSE-MIT %{buildroot}%{_licensedir}/solidcraft/LICENSE-MIT
install -Dm644 payload/usr/share/doc/solidcraft/NOTICE %{buildroot}%{_licensedir}/solidcraft/NOTICE
install -Dm644 payload/usr/share/doc/solidcraft/README.md %{buildroot}%{_docdir}/solidcraft/README.md
install -Dm644 payload/usr/share/doc/solidcraft/THIRD-PARTY-LICENSES.txt %{buildroot}%{_docdir}/solidcraft/THIRD-PARTY-LICENSES.txt
install -Dm644 payload/usr/share/icons/hicolor/128x128/apps/ai.storyteller.solidcraft.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.storyteller.solidcraft.png
install -Dm644 payload/usr/share/icons/hicolor/16x16/apps/ai.storyteller.solidcraft.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/ai.storyteller.solidcraft.png
install -Dm644 payload/usr/share/icons/hicolor/24x24/apps/ai.storyteller.solidcraft.png %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/ai.storyteller.solidcraft.png
install -Dm644 payload/usr/share/icons/hicolor/256x256/apps/ai.storyteller.solidcraft.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.storyteller.solidcraft.png
install -Dm644 payload/usr/share/icons/hicolor/32x32/apps/ai.storyteller.solidcraft.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.storyteller.solidcraft.png
install -Dm644 payload/usr/share/icons/hicolor/48x48/apps/ai.storyteller.solidcraft.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/ai.storyteller.solidcraft.png
install -Dm644 payload/usr/share/icons/hicolor/512x512/apps/ai.storyteller.solidcraft.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.storyteller.solidcraft.png
install -Dm644 payload/usr/share/icons/hicolor/64x64/apps/ai.storyteller.solidcraft.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.storyteller.solidcraft.png
install -Dm644 payload/usr/share/metainfo/ai.storyteller.solidcraft.metainfo.xml %{buildroot}%{_datadir}/metainfo/ai.storyteller.solidcraft.metainfo.xml
install -Dm644 payload/usr/share/mime/packages/ai.storyteller.solidcraft.xml %{buildroot}%{_datadir}/mime/packages/ai.storyteller.solidcraft.xml

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
%license %{_licensedir}/solidcraft/LICENSE-APACHE
%license %{_licensedir}/solidcraft/LICENSE-MIT
%license %{_licensedir}/solidcraft/NOTICE
%doc %{_docdir}/solidcraft/README.md
%doc %{_docdir}/solidcraft/THIRD-PARTY-LICENSES.txt
%{_bindir}/solidcraft
%{_bindir}/solidcraft-cli
%{_bindir}/solvecraft-cli
%{_datadir}/applications/ai.storyteller.solidcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.solidcraft.png
%{_datadir}/metainfo/ai.storyteller.solidcraft.metainfo.xml
%{_datadir}/mime/packages/ai.storyteller.solidcraft.xml

%changelog
* Sun Oct 25 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.22.1-1
- update to 0.22.1

* Sat Oct 24 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.22.0-1
- initial COPR package (rebundle of the upstream RPM)
