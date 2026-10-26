Name:           xwayland-satellite
Version:        0.8.3
Release:        1%{?dist}
Summary:        Rootless Xwayland integration for Wayland compositors
License:        MPL-2.0
URL:            https://github.com/Supreeeme/xwayland-satellite
Source0:        https://github.com/Supreeeme/xwayland-satellite/archive/refs/tags/v%{version}/xwayland-satellite-%{version}.tar.gz
# The Rust dependencies are vendored into a tarball, so the build itself
# does not need the network. The tarball is generated from Source0 by the
# packages workflow (and by the Makefile, for the local builds).
Source1:        xwayland-satellite-vendor.tar.xz
# The unit file of upstream starts the binary from /usr/local/bin, where
# it is not installed.
Patch1:         0001-fix-executable-path-in-systemd-unit.patch

BuildRequires:  cargo-rpm-macros
# The font is loaded through fontconfig, which is bound with bindgen, so a
# C compiler and libclang are needed.
BuildRequires:  clang
BuildRequires:  gcc
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(xcb-cursor)
BuildRequires:  systemd-rpm-macros

# Satellite drives the Xwayland server, so it is needed at runtime.
Requires:       xorg-x11-server-Xwayland
# The decoration font is loaded through fontconfig at runtime.
Requires:       font(opensans)

%description
xwayland-satellite grants rootless Xwayland integration to any Wayland
compositor implementing xdg_wm_base and viewporter. It is useful for
compositors that do not want to implement rootless Xwayland support
themselves: satellite acts as the X window manager and hosts the Xwayland
server inside the Wayland session.

The package ships the xwayland-satellite binary, a systemd user service
that starts it with the graphical session, and the manual page.

%prep
# The patches are applied with a strip level of 1, so the paths of the
# patch files (a/... and b/...) are removed.
%autosetup -n xwayland-satellite-%{version} -p1

# Unpack the vendored Rust dependencies next to the sources: the directory
# name has to match the one the cargo_prep macro points cargo at.
tar -xf %{SOURCE1}

# Point cargo at the vendored dependencies and use the release profile of
# the RPM macros.
%cargo_prep -v vendor

# The decoration font is loaded through fontconfig at runtime, so it does
# not have to be embedded into the binary.
rm -f OpenSans-Regular.ttf

%build
%cargo_build -f systemd,fontconfig

%check
# The integration tests need a running Wayland session, so only the unit
# tests are run here.
%cargo_test -f systemd,fontconfig -- --lib

%install
install -Dm755 target/rpm/xwayland-satellite %{buildroot}%{_bindir}/xwayland-satellite
install -Dm644 resources/xwayland-satellite.service %{buildroot}%{_userunitdir}/xwayland-satellite.service
install -Dm644 xwayland-satellite.man %{buildroot}%{_mandir}/man1/xwayland-satellite.1
install -Dm644 LICENSE %{buildroot}%{_licensedir}/xwayland-satellite/LICENSE
install -Dm644 README.md %{buildroot}%{_docdir}/xwayland-satellite/README.md

%post
%systemd_user_post xwayland-satellite.service

%preun
%systemd_user_preun xwayland-satellite.service

%postun
%systemd_user_postun_with_reload xwayland-satellite.service

%files
%license %{_licensedir}/xwayland-satellite/LICENSE
%doc %{_docdir}/xwayland-satellite/README.md
%{_bindir}/xwayland-satellite
%{_userunitdir}/xwayland-satellite.service
%{_mandir}/man1/xwayland-satellite.1*

%changelog
* Mon Oct 26 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.8.3-1
- initial COPR package
