# cs9711-fingerprint — https://github.com/mmhfarooque/chipsailing-cs9711-fingerprint-linux

[![License: LGPL-2.1-or-later AND MIT](https://img.shields.io/badge/License-LGPL--2.1--or--later%20AND%20MIT-blue.svg)](https://github.com/mmhfarooque/chipsailing-cs9711-fingerprint-linux/blob/main/LICENSE)

Driver and graphical manager for the Chipsailing CS9711 USB fingerprint
scanner (`2541:0236`), a cheap sensor that the stock libfprint does
not support.

The package ships a libfprint with the driver of the scanner, built
from the community fork that adds it, and the GTK4 manager of the
project, which enrolls the fingers and configures the authentication.

## Setup

```sh
sudo dnf install cs9711-fingerprint
```

Then plug the scanner in and enroll a finger — 15 touches are needed:

```sh
fprintd-enroll
fprintd-verify
```

The authentication is enabled with `authselect`, the way the
distribution does it, so the fingerprint works for the login, for the
lock screen and for `sudo`. The manager is in the menu of the desktop
(it is called *CS9711 Fingerprint Manager*), or it can be started with:

```sh
cs9711-manager
```

## Files

| File | Purpose |
|---|---|
| `cs9711-manager` | The launcher of the manager |
| `/usr/libexec/cs9711-fingerprint/` | The manager and its data: the version, the helpers and the patch of the project |
| `/usr/local/lib64/libfprint-2.so.2` | The library with the driver of the CS9711 |
| `/etc/ld.so.conf.d/00-cs9711-local.conf` | The search path of the linker, so the driver takes precedence |
| `cs9711-manager.desktop` | The desktop entry of the manager |

## Notes

**The driver is built with all the default drivers of libfprint**, so
the other fingerprint readers of the machine keep working: the CS9711
is added to the ones the distribution ships, not put in their place.

**The library is installed in `/usr/local`**, the private tree of the
local software, and the directory is added to the search path of the
linker with a drop-in of `/etc/ld.so.conf.d`. The library of the
distribution is not replaced and not removed: the driver of this
package takes precedence over it, and removing the package restores it
at once.

The library is the one of the fork of the project, built from the
sources of libfprint with the driver of the CS9711 and with the retry
delay of the project (1500ms between two attempts, so there is time to
reposition the finger). The commit of the fork is pinned in the spec:
the fork has no releases, so the build has to produce the same library
every time.

The GObject introspection data of the library is the one of the
distribution: `girepository` only looks for it in the directories of
the distribution, and the API of both is the same.

**The retry delay is fixed at 1500ms.** The manager can change it, but
only when the sources of the driver are next to it — which is the case
of the installation of the project, not of this package.

**The buttons of the maintenance section of the manager** ("Rebuild
Driver" and "Uninstall Driver") do not fit a packaged installation: the
driver is built by the package, and the uninstall of the manager
removes the library of the package. Reinstall the package to get it
back.

**OpenCV is the weak spot of the driver.** The library is linked
against the OpenCV of the distribution, and the name of its major
version changes when the distribution moves to the next one: the driver
has to be rebuilt against it. Update the package when that happens.

Upstream: <https://github.com/mmhfarooque/chipsailing-cs9711-fingerprint-linux>
