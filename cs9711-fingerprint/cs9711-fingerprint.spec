# The build needs meson, a C toolchain and the development packages of
# the libraries of the driver, so the Makefile builds the package in a
# container: the host does not need them.
# build-in-container

Name:           cs9711-fingerprint
Version:        2.2.4
Release:        1%{?dist}
Summary:        Driver and manager for the Chipsailing CS9711 fingerprint scanner
License:        LGPL-2.1-or-later AND MIT
URL:            https://github.com/mmhfarooque/chipsailing-cs9711-fingerprint-linux
# The project: the graphical manager, its helpers and the documentation.
Source0:        https://github.com/mmhfarooque/chipsailing-cs9711-fingerprint-linux/archive/refs/tags/v%{version}.tar.gz
# The driver: a fork of libfprint with the driver of the CS9711. The
# commit is pinned because the fork has no releases: the build has to
# produce the same library every time. Bump it to follow the fork.
Source1:        https://github.com/archeYR/libfprint-CS9711/archive/3c93fc2da6347624fc9c2d2f36a38fec64f99835.tar.gz
# The tests of the driver need doctest, which Fedora does not ship with a
# pkg-config file. They are not needed to build the driver itself.
Source2:        cs9711-optional-doctest.patch
# The launcher of the manager: the path of the manager is rewritten at
# install time, so it is not hardcoded here.
Source3:        cs9711-manager-launcher
# The script the manager runs when the user asks for a rebuild of the
# driver. The driver is shipped by this package, so a rebuild is an
# update of the package.
Source4:        cs9711-reinstall

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(cairo)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(gobject-introspection-1.0)
BuildRequires:  pkgconfig(gudev-1.0)
BuildRequires:  pkgconfig(gusb)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(udev)
# The package is used instead of the pkg-config name of OpenCV: the
# driver resolves it as "opencv4", then "opencv5", and the name of the
# major version changes when the distribution moves to the next one.
BuildRequires:  opencv-devel

# The daemon that talks to the driver, and the PAM module that
# authenticates the user with a fingerprint.
Requires:       fprintd
Requires:       fprintd-pam
# The introspection data of the library is the one of the distribution:
# girepository only looks for it in the directories of the distribution,
# and the API of both libraries is the same.
Requires:       libfprint
# The manager is a GTK4 application written in Python.
Recommends:     gtk4
Recommends:     libadwaita
Recommends:     python3-gobject
# The helper that unlocks the GNOME keyring with the password of the
# user talks to the secret service of the session.
Recommends:     python3-dbus
# The PAM configuration is done with authselect, the way the
# distribution does it.
Recommends:     authselect

%description
The Chipsailing CS9711 is a cheap USB fingerprint scanner that the
stock libfprint does not support. This package ships a libfprint with
the driver of the scanner, built from the community fork that adds it,
and the graphical manager of the project, which enrolls the fingers and
configures the authentication.

The driver is built with all the default drivers of libfprint, so the
other fingerprint readers of the machine keep working: the CS9711 is
added to the ones the distribution ships, not put in their place.

The library is installed in the private tree of /usr/local and the
directory is added to the search path of the linker, so the driver
takes precedence over the one of the distribution without replacing
it. Removing the package restores the library of the distribution.

%prep
# The project: the manager, its helpers and the documentation.
%setup -q -n chipsailing-cs9711-fingerprint-linux-%{version}

# The driver: the fork of libfprint with the driver of the CS9711.
mkdir libfprint-CS9711
tar -xf %{SOURCE1} --strip-components=1 -C libfprint-CS9711

# The retry delay of the project: the 250ms of the driver are too fast
# to reposition the finger between two attempts.
patch -p1 -d libfprint-CS9711 < patches/cs9711-retry-delay-1500ms.patch

# The tests of the driver need doctest, which is not needed to build it.
patch -p1 -d libfprint-CS9711 < %{SOURCE2}

%build
# The driver is built with the default set of drivers of libfprint, so
# the fingerprint readers of the machine keep working. The CS9711 is one
# of them: the fork adds it to the default set.
#
# The udev rules and the hwdb of the distribution are not installed:
# they are the ones of the libfprint of the distribution, and the rules
# of the devices are not needed for a USB scanner.
meson setup libfprint-CS9711/builddir libfprint-CS9711 \
    --prefix=/usr/local \
    --libdir=lib64 \
    -Ddrivers=default \
    -Dudev_rules=disabled \
    -Dudev_hwdb=disabled \
    -Ddoc=false \
    -Dinstalled-tests=false \
    -Dgtk-examples=false
meson compile -C libfprint-CS9711/builddir

%check
# The tests of the drivers need the hardware of each one of them, so
# only the unit tests are run here.
meson test -C libfprint-CS9711/builddir

%install
DESTDIR=%{buildroot} meson install -C libfprint-CS9711/builddir

# Only the library is shipped: the headers, the pkg-config file and the
# introspection data belong to the development package of the
# distribution, which has its own copy of them. The typelib is not
# shipped either: girepository looks for it in the directories of the
# distribution, where the one of the libfprint of the distribution
# describes the same API.
rm -rf %{buildroot}/usr/local/include
rm -rf %{buildroot}/usr/local/lib64/girepository-1.0
rm -rf %{buildroot}/usr/local/lib64/pkgconfig
rm -rf %{buildroot}/usr/local/sbin
rm -rf %{buildroot}/usr/local/share

# The manager and its data. The manager looks for them in the directory
# of its own script, so they all sit next to it.
install -Dm755 cs9711-manager.py \
    %{buildroot}%{_libexecdir}/cs9711-fingerprint/cs9711-manager.py
install -Dm644 VERSION \
    %{buildroot}%{_libexecdir}/cs9711-fingerprint/VERSION
install -Dm755 helpers/set-empty-keyring-password.py \
    %{buildroot}%{_libexecdir}/cs9711-fingerprint/helpers/set-empty-keyring-password.py
install -Dm644 helpers/link-path.sh \
    %{buildroot}%{_libexecdir}/cs9711-fingerprint/helpers/link-path.sh
install -Dm644 helpers/opencv-flex.sh \
    %{buildroot}%{_libexecdir}/cs9711-fingerprint/helpers/opencv-flex.sh
install -Dm644 patches/cs9711-retry-delay-1500ms.patch \
    %{buildroot}%{_libexecdir}/cs9711-fingerprint/patches/cs9711-retry-delay-1500ms.patch
install -Dm755 %{SOURCE4} \
    %{buildroot}%{_libexecdir}/cs9711-fingerprint/reinstall.sh

# The launcher of the manager: it runs the manager with the path of the
# private directory of the package.
sed 's|^exec .*|exec %{_libexecdir}/cs9711-fingerprint/cs9711-manager.py "$@"|' \
    %{SOURCE3} \
    | install -Dm755 /dev/stdin %{buildroot}%{_bindir}/cs9711-manager

# The desktop entry of the manager: the template of the project runs
# the manager from its own directory and points to the icon of that
# directory, neither of which is the case here. The categories of the
# template are three main ones, which would put the manager twice in the
# menu of the desktop.
sed -e '/^#/d' \
    -e 's|^Exec=.*|Exec=cs9711-manager|' \
    -e 's|^Icon=.*|Icon=cs9711-manager|' \
    -e 's|^Categories=.*|Categories=Settings;HardwareSettings;|' \
    cs9711-manager.desktop \
    | install -Dm644 /dev/stdin %{buildroot}%{_datadir}/applications/cs9711-manager.desktop

install -Dm644 assets/cs9711-manager.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/cs9711-manager.svg

install -Dm644 LICENSE %{buildroot}%{_licensedir}/cs9711-fingerprint/LICENSE
install -Dm644 libfprint-CS9711/COPYING \
    %{buildroot}%{_licensedir}/cs9711-fingerprint/COPYING
install -Dm644 README.md %{buildroot}%{_docdir}/cs9711-fingerprint/README.md
install -Dm644 CHANGELOG.md %{buildroot}%{_docdir}/cs9711-fingerprint/CHANGELOG.md
install -Dm644 COMPAT-CHECKLIST.md \
    %{buildroot}%{_docdir}/cs9711-fingerprint/COMPAT-CHECKLIST.md

%post
# The desktop entry and the icon of the manager have to be added to the
# caches of the desktop. Every helper is optional, so a missing one is
# simply skipped.
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q %{_datadir}/applications || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f %{_datadir}/icons/hicolor || :
fi

# The linker of the distribution does not look into /usr/local, so the
# directory of the driver is added to its search path. The drop-in is
# removed when the package is removed.
printf '# Added by cs9711-fingerprint. Removed on uninstall.\n/usr/local/lib64\n' \
    > /etc/ld.so.conf.d/00-cs9711-local.conf
chmod 644 /etc/ld.so.conf.d/00-cs9711-local.conf
ldconfig

# The daemon has to pick up the new library.
systemctl try-restart fprintd.service >/dev/null 2>&1 || :

# The fingerprint is enabled for the authentication with authselect,
# the way the distribution does it: the feature adds pam_fprintd to the
# stack of the system authentication. It is only enabled when it is
# not enabled already, and it is disabled again when the package is
# removed.
if command -v authselect >/dev/null 2>&1 &&
   authselect current >/dev/null 2>&1 &&
   ! authselect current 2>/dev/null | grep -q with-fingerprint
then
    if authselect enable-feature with-fingerprint >/dev/null 2>&1; then
        mkdir -p /var/lib/cs9711-fingerprint
        touch /var/lib/cs9711-fingerprint/pam-feature
        authselect apply >/dev/null 2>&1 || :
    fi
fi

cat <<'EOF'

The driver of the Chipsailing CS9711 is installed.

Enroll a finger with:

  fprintd-enroll

15 touches are needed. The manager of the project is in the menu of the
desktop, or it can be started with 'cs9711-manager'.

The fingerprint is enabled for the authentication with authselect. When
it is not, enable it with:

  sudo authselect enable-feature with-fingerprint
  sudo authselect apply

EOF

%postun
# The caches of the desktop have to be refreshed again, the entry of the
# manager is gone.
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q %{_datadir}/applications || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f %{_datadir}/icons/hicolor || :
fi

# The library is gone: the linker has to forget it and the daemon has
# to go back to the library of the distribution.
if [ "$1" -eq 0 ]; then
    rm -f /etc/ld.so.conf.d/00-cs9711-local.conf
fi
ldconfig
systemctl try-restart fprintd.service >/dev/null 2>&1 || :

# The feature of authselect is disabled again, but only when this
# package is the one that enabled it.
if [ "$1" -eq 0 ] && [ -f /var/lib/cs9711-fingerprint/pam-feature ]; then
    rm -f /var/lib/cs9711-fingerprint/pam-feature
    rmdir /var/lib/cs9711-fingerprint 2>/dev/null || :
    if command -v authselect >/dev/null 2>&1; then
        authselect disable-feature with-fingerprint >/dev/null 2>&1 || :
        authselect apply >/dev/null 2>&1 || :
    fi
fi

%files
%license %{_licensedir}/cs9711-fingerprint/COPYING
%license %{_licensedir}/cs9711-fingerprint/LICENSE
%doc %{_docdir}/cs9711-fingerprint/CHANGELOG.md
%doc %{_docdir}/cs9711-fingerprint/COMPAT-CHECKLIST.md
%doc %{_docdir}/cs9711-fingerprint/README.md
%{_bindir}/cs9711-manager
%{_datadir}/applications/cs9711-manager.desktop
%{_datadir}/icons/hicolor/scalable/apps/cs9711-manager.svg
%{_libexecdir}/cs9711-fingerprint/cs9711-manager.py
%{_libexecdir}/cs9711-fingerprint/VERSION
%{_libexecdir}/cs9711-fingerprint/helpers/link-path.sh
%{_libexecdir}/cs9711-fingerprint/helpers/opencv-flex.sh
%{_libexecdir}/cs9711-fingerprint/helpers/set-empty-keyring-password.py
%{_libexecdir}/cs9711-fingerprint/patches/cs9711-retry-delay-1500ms.patch
%{_libexecdir}/cs9711-fingerprint/reinstall.sh
/usr/local/lib64/libfprint-2.so
/usr/local/lib64/libfprint-2.so.2
/usr/local/lib64/libfprint-2.so.2.0.0

%changelog
* Thu Nov 12 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 2.2.4-1
- initial COPR package
