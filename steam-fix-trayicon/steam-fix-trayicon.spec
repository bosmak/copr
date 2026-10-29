%global debug_package %{nil}

Name:           steam-fix-trayicon
Version:        0.1.0
Release:        3%{?dist}
Summary:        Replacement Steam tray icon: double click opens the Steam window
License:        MIT
URL:            https://github.com/bosmak/copr/tree/main/steam-fix-trayicon
# Our own sources, shipped verbatim from this repository.
Source0:        steam-fix-trayicon.py
Source1:        steam-fix-trayicon.service
Source2:        99-steam-fix-trayicon.conf
Source3:        LICENSE

# Needed for the systemd user unit macros.
BuildRequires:  systemd-rpm-macros

Requires:       python3-dbus
Requires:       python3-gobject
Requires:       systemd
# The scriptlets of the package use runuser (from util-linux) to reach the
# user manager of the logged in users. systemd only requires util-linux-core,
# which does not ship runuser, so util-linux is needed explicitly.
Requires:       util-linux

# quickshell provides the tray IPC that the shell (DankMaterialShell) exposes
# to render the menu on a single click.  Without it the icon still shows and
# the double click still works, only the single-click menu is unavailable.
Recommends:     quickshell
# The client the replacement icon belongs to.
Recommends:     steam

%description
Replaces Steam's own system tray icon on Wayland desktops with one that
behaves the way people expect:

  * single click  - opens Steam's own menu (recently played games, Store,
                    Library, Community, Friends, Settings, Exit)
  * double click  - opens or focuses the Steam window
  * right click   - same menu

Steam's Linux tray icon is an AppIndicator (libappindicator / ayatana).  The
panel always answers a click with the application's menu, so the Steam window
can never be opened from the tray icon.  That is Valve's own open feature
request: https://github.com/ValveSoftware/steam-for-linux/issues/3519

This package installs a small StatusNotifierItem that mirrors Steam's icon,
tooltip and menu, plus a systemd user service that keeps it running and
re-registers it with the panel whenever the shell restarts.

This package is developed against DuxShell (formerly DankMaterialShell / DMS)
and has only been tested on niri.  DuxShell can run on other Wayland
compositors, but that combination is untested: the single-click menu is
opened through DuxShell's own tray IPC, and the double click relies on the
panel sending Activate() on every left click.

%prep
# Nothing to prepare — all sources are plain files shipped in this repo.

%build
# Nothing to build — we ship a single Python script.

%install
install -Dm755 %{SOURCE0} %{buildroot}%{_bindir}/steam-fix-trayicon
install -Dm644 %{SOURCE1} %{buildroot}%{_userunitdir}/steam-fix-trayicon.service
# Drop-in for DankMaterialShell: hides Valve's original indicator (id
# "steam") so only the replacement one shows up in the tray.
install -Dm644 %{SOURCE2} %{buildroot}%{_userunitdir}/dms.service.d/99-steam-fix-trayicon.conf
install -Dm644 %{SOURCE3} %{buildroot}%{_licensedir}/steam-fix-trayicon/LICENSE

%post
# Standard user-unit handling for the invoking user.
%systemd_user_post steam-fix-trayicon.service

%posttrans
# This runs at the very end of the transaction, after the pre-uninstall and
# post-uninstall scriptlets of the package we are replacing.  Those old
# scriptlets stop and disable the user service, so this is where the service
# has to be enabled and started again - doing it in the post scriptlet was
# not enough, the next `dnf update` killed the icon again.
#
# The scriptlets run as root, so they cannot reach the user manager of the
# person who is actually logged in.  Enable and start the service for every
# user that currently has a session, then restart the shell so the
# DMS drop-in (which hides Valve's original icon) takes effect.
enabled_user=''

for uid in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $1}'); do
    # Skip uid 0 on purpose: while `sudo dnf` runs, the root user has a
    # session of its own (created by pam_systemd), and the indicator would
    # be started in root's user manager, where the shell's
    # StatusNotifierWatcher does not exist.
    [ "$uid" -ne 0 ] || continue
    user=$(getent passwd "$uid" | cut -d: -f1)
    [ -n "$user" ] || continue
    runtime=$(loginctl show-user "$uid" --property=RuntimePath --value 2>/dev/null)
    [ -n "$runtime" ] && [ -d "$runtime" ] || continue
    runuser -u "$user" -- env XDG_RUNTIME_DIR="$runtime" \
        DBUS_SESSION_BUS_ADDRESS="unix:path=$runtime/bus" \
        systemctl --user enable --now steam-fix-trayicon.service >/dev/null 2>&1 || :
    runuser -u "$user" -- env XDG_RUNTIME_DIR="$runtime" \
        DBUS_SESSION_BUS_ADDRESS="unix:path=$runtime/bus" \
        systemctl --user try-restart dms.service >/dev/null 2>&1 || :
    if runuser -u "$user" -- env XDG_RUNTIME_DIR="$runtime" \
        DBUS_SESSION_BUS_ADDRESS="unix:path=$runtime/bus" \
        systemctl --user is-enabled steam-fix-trayicon.service >/dev/null 2>&1; then
        enabled_user="$user"
    fi
done

if [ -n "$enabled_user" ]; then
    status="enabled — running now (user $enabled_user)"
else
    status='NOT enabled yet (no active user session; run the commands below)'
fi

cat <<EOF

================================================================
 steam-fix-trayicon %{version} — USER service, not a system service!
================================================================

  Use:  systemctl --user status steam-fix-trayicon.service
  Not:  systemctl       status steam-fix-trayicon.service  <- won't find it

  Status: $status

  Tray behaviour now:
    single click  -> Steam's menu (recently played games, Store, ...)
    double click  -> opens / focuses the Steam window
    right click   -> Steam's menu

  To enable and start it manually (if not already done):

         systemctl --user enable --now steam-fix-trayicon.service

  To go back to Valve's original tray icon:

         sudo rm /usr/lib/systemd/user/dms.service.d/99-steam-fix-trayicon.conf
         systemctl --user daemon-reload && systemctl --user restart dms.service
         systemctl --user disable --now steam-fix-trayicon.service

  Verify with:   systemctl --user status steam-fix-trayicon.service
================================================================
EOF

%preun
%systemd_user_preun steam-fix-trayicon.service

# Stop and disable the service for the users that have it enabled.
# $1 is the number of copies of this package that stay installed: it is 1
# during an upgrade and 0 when the package is really removed.  Only a real
# removal may stop the service - during an upgrade this used to kill the
# icon that the post-transaction scriptlet had just started.
if [ "$1" -eq 0 ]; then
    for uid in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $1}'); do
        [ "$uid" -ne 0 ] || continue
        user=$(getent passwd "$uid" | cut -d: -f1)
        [ -n "$user" ] || continue
        runtime=$(loginctl show-user "$uid" --property=RuntimePath --value 2>/dev/null)
        [ -n "$runtime" ] && [ -d "$runtime" ] || continue
        runuser -u "$user" -- env XDG_RUNTIME_DIR="$runtime" \
            DBUS_SESSION_BUS_ADDRESS="unix:path=$runtime/bus" \
            systemctl --user disable --now steam-fix-trayicon.service >/dev/null 2>&1 || :
    done
fi

%postun
%systemd_user_postun steam-fix-trayicon.service

%files
%license %{_licensedir}/steam-fix-trayicon/LICENSE
%{_bindir}/steam-fix-trayicon
%{_userunitdir}/steam-fix-trayicon.service
%{_userunitdir}/dms.service.d/99-steam-fix-trayicon.conf

%changelog
* Wed Oct 28 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.1.0-3
- keep the indicator alive across package upgrades: enable and start it from
  the post-transaction scriptlet (the last one of the transaction) and only
  stop it when the package is really removed
- skip uid 0 in the scriptlet loops: during `sudo dnf` the root user has a
  session, and the indicator was started in root's user manager, where the
  shell's StatusNotifierWatcher does not exist

* Sat Oct 24 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.1.0-2
- document that this is made for DuxShell (formerly DankMaterialShell) and
  only tested on niri

* Sat Oct 24 2026 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.1.0-1
- initial COPR package
