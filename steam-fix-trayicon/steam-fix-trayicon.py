#!/usr/bin/env python3
"""Replacement Steam tray icon (StatusNotifierItem).

    single click  ->  Steam's own menu (proxied from Steam's dbusmenu)
    double click  ->  opens / focuses the Steam window
    right click   ->  same menu

Steam's Linux tray icon is a libappindicator item, so the panel always
answers a click with Steam's popup menu and the window can never be opened
from the tray - https://github.com/ValveSoftware/steam-for-linux/issues/3519

The icon follows Steam: it is registered with the panel's watcher while the
Steam client runs and taken out of the tray when the client exits.

See the package README for the full story.  Requires python3 + python3-dbus.
"""

import os
import re
import subprocess
import sys
import time

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

SNI_IFACE = "org.kde.StatusNotifierItem"
MENU_IFACE = "com.canonical.dbusmenu"
PROPS_IFACE = "org.freedesktop.DBus.Properties"
WATCHER_IFACE = "org.kde.StatusNotifierWatcher"

WATCHER_NAME = "org.kde.StatusNotifierWatcher"
WATCHER_PATH = "/StatusNotifierWatcher"

ITEM_PATH = "/StatusNotifierItem"
MENU_PATH = "/MenuBar"
# The bus name the indicator is registered under.  It is a well-known name
# of our own (and not the unique name of the connection) because the
# watcher spec has no "unregister" method: an item is dropped when the bus
# name it was registered under disappears.  Releasing this name is what
# takes the icon out of the tray.
BUS_NAME = "org.kde.StatusNotifierItem-steam-window"
QUALIFIED_ITEM = BUS_NAME + ITEM_PATH

CFG = {
    # Two Activate() calls closer together than this count as a double click.
    "double_click_ms": int(os.environ.get("STEAM_TRAY_DOUBLE_CLICK_MS", "450")),
    # How long a single click waits for a second one before the menu opens.
    "menu_delay_ms": int(os.environ.get("STEAM_TRAY_MENU_DELAY_MS", "280")),
    "steam_bin": os.environ.get("STEAM_TRAY_STEAM_BIN", "steam"),
    "window_url": os.environ.get("STEAM_TRAY_WINDOW_URL", "steam://open/main"),
    "icon_name": os.environ.get("STEAM_TRAY_ICON_NAME", "steam_tray_mono"),
    "icon_path": os.environ.get(
        "STEAM_TRAY_ICON_PATH", os.path.expanduser("~/.local/share/Steam/public")
    ),
    # Must differ from Steam's own item id ("steam"), otherwise hiding one
    # hides both.
    "item_id": os.environ.get("STEAM_TRAY_ITEM_ID", "steam-window"),
}

# The processes we started, so they can be reaped when they are done.
SPAWNED = []

# Fallback menu, used while Steam is not running.
FALLBACK_ITEMS = [
    (1, "Open Steam", ["steam://open/main"]),
    (2, "Library", ["steam://open/games"]),
    (3, "Store", ["steam://store"]),
    (4, "Community", ["steam://url/CommunityHome/"]),
    (5, "Friends", ["steam://open/friends"]),
    (6, "Exit Steam", ["-shutdown"]),
]


def log(msg):
    print(f"[steam-fix-trayicon] {msg}", file=sys.stderr, flush=True)


def proc_comm(pid):
    """The command name of a process, read from /proc."""
    try:
        with open(f"/proc/{pid}/comm") as fh:
            return fh.read().strip()
    except OSError:
        return None


def proc_state(pid):
    """The state of a process ("R", "S", "Z", ...) read from /proc."""
    try:
        with open(f"/proc/{pid}/stat") as fh:
            data = fh.read()
    except OSError:
        return None
    # The comm field may contain spaces and parentheses, so the fields
    # after the last closing parenthesis are the reliable ones.
    try:
        return data[data.rindex(")") + 1 :].split()[0]
    except (ValueError, IndexError):
        return None


def steam_running():
    """Whether the Steam client is running.

    The client is the process named "steam" - the launcher script and the
    web helpers have their own names.  Zombies are ignored: a Steam that
    was started here and that exited without being reaped would keep the
    icon around forever.
    """
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        if proc_comm(pid) != "steam":
            continue
        if proc_state(pid) == "Z":
            continue
        return True
    return False


def reap_children():
    """Reap the processes we started, so they do not linger as zombies."""
    for proc in list(SPAWNED):
        if proc.poll() is not None:
            SPAWNED.remove(proc)


def launch(args):
    """Run a steam CLI command without blocking the main loop."""
    cmd = [CFG["steam_bin"]] + list(args)
    log(f"launching: {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        log(f"failed to launch {cmd[0]}: {exc}")
        return
    SPAWNED.append(proc)


def dms_instances():
    """Ids of the running quickshell instances that host the DMS shell."""
    try:
        out = subprocess.run(
            ["quickshell", "list", "--all"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        ).stdout.decode(errors="replace")
    except (OSError, subprocess.SubprocessError):
        return []
    ids = []
    current = None
    for line in out.splitlines():
        m = re.match(r"^Instance (\S+):", line.strip())
        if m:
            current = m.group(1)
            continue
        if current and "dms" in line.lower():
            ids.append(current)
            current = None
    return ids


def dms_open_menu(item_id):
    """Ask DMS to render the tray menu of item_id (the host side menu)."""
    for inst in dms_instances():
        try:
            res = subprocess.run(
                ["quickshell", "ipc", "-i", inst, "call", "tray", "menu", item_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            log(f"could not reach DMS instance {inst}: {exc}")
            continue
        if b"SUCCESS" in res.stdout:
            return True
    log(f"could not ask DMS to open the menu for {item_id}")
    return False


class SteamTrayMenu(dbus.service.Object):
    """com.canonical.dbusmenu implementation.

    When Steam is running the calls are proxied to Steam's own menu, so the
    panel shows Steam's real menu (recently played games, Store, Library,
    Community, Friends, Settings, Big Picture, SteamVR, Exit Steam).
    """

    def __init__(self, bus):
        dbus.service.Object.__init__(self, bus, MENU_PATH)
        self._bus = bus
        self._remote = None

    def set_remote(self, service, path):
        """Point the menu at Steam's own dbusmenu."""
        if not service or not path:
            self._remote = None
            return
        try:
            self._remote = dbus.Interface(
                self._bus.get_object(service, path), MENU_IFACE
            )
            log(f"menu proxied to {service}{path}")
        except dbus.DBusException as exc:
            self._remote = None
            log(f"could not proxy menu: {exc}")

    # --- helpers for the fallback menu ---
    def _fallback_props(self, label):
        return dbus.Dictionary(
            {
                "type": dbus.String("standard"),
                "label": dbus.String(label),
                "enabled": dbus.Boolean(True),
                "visible": dbus.Boolean(True),
            },
            signature="sv",
        )

    def _fallback_layout(self):
        children = dbus.Array([], signature="(ia{sv}av)")
        for item_id, label, _args in FALLBACK_ITEMS:
            children.append(
                dbus.Struct(
                    (
                        dbus.Int32(item_id),
                        self._fallback_props(label),
                        dbus.Array([], signature="(ia{sv}av)"),
                    ),
                    signature="(ia{sv}av)",
                )
            )
        return dbus.Struct(
            (
                dbus.Int32(0),
                dbus.Dictionary({}, signature="sv"),
                children,
            ),
            signature="(ia{sv}av)",
        )

    # --- dbusmenu interface ---
    @dbus.service.method(MENU_IFACE, in_signature="iias", out_signature="u(ia{sv}av)")
    def GetLayout(self, parent_id, recursion_depth, property_names):
        if self._remote is not None:
            try:
                return self._remote.GetLayout(
                    parent_id, recursion_depth, property_names
                )
            except dbus.DBusException as exc:
                log(f"GetLayout proxy failed: {exc}")
        return dbus.UInt32(1), self._fallback_layout()

    @dbus.service.method(MENU_IFACE, in_signature="asas", out_signature="a{ia{sv}}")
    def GetGroupProperties(self, ids, property_names):
        if self._remote is not None:
            try:
                return self._remote.GetGroupProperties(ids, property_names)
            except dbus.DBusException as exc:
                log(f"GetGroupProperties proxy failed: {exc}")
        out = dbus.Dictionary({}, signature="ia{sv}")
        for item_id, label, _args in FALLBACK_ITEMS:
            if int(item_id) in [int(i) for i in ids]:
                out[int(item_id)] = self._fallback_props(label)
        return out

    @dbus.service.method(MENU_IFACE, in_signature="is", out_signature="v")
    def GetProperty(self, item_id, name):
        if self._remote is not None:
            try:
                return self._remote.GetProperty(item_id, name)
            except dbus.DBusException as exc:
                log(f"GetProperty proxy failed: {exc}")
        for iid, label, _args in FALLBACK_ITEMS:
            if iid == item_id:
                if name == "label":
                    return dbus.String(label)
                if name == "type":
                    return dbus.String("standard")
                if name in ("enabled", "visible"):
                    return dbus.Boolean(True)
        return dbus.String("")

    @dbus.service.method(MENU_IFACE, in_signature="isvu", out_signature="")
    def Event(self, item_id, event_id, data, timestamp):
        if self._remote is not None:
            try:
                self._remote.Event(item_id, event_id, data, timestamp)
                return
            except dbus.DBusException as exc:
                log(f"Event proxy failed: {exc}")
        if event_id != "clicked":
            return
        for iid, _label, args in FALLBACK_ITEMS:
            if iid == item_id:
                launch(args)
                return

    @dbus.service.method(MENU_IFACE, in_signature="i", out_signature="b")
    def AboutToShow(self, item_id):
        if self._remote is not None:
            try:
                return self._remote.AboutToShow(item_id)
            except dbus.DBusException as exc:
                log(f"AboutToShow proxy failed: {exc}")
        return dbus.Boolean(False)

    # Some hosts (quickshell) probe the menu object for properties.
    @dbus.service.method(PROPS_IFACE, in_signature="ss", out_signature="v")
    def Get(self, interface_name, prop_name):
        return dbus.String("")

    @dbus.service.method(PROPS_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface_name):
        return dbus.Dictionary({}, signature="sv")


class SteamTrayItem(dbus.service.Object):
    """The StatusNotifierItem that replaces Steam's own tray icon."""

    def __init__(self, bus):
        dbus.service.Object.__init__(self, bus, ITEM_PATH)
        self._title = "Steam"
        self._description = "Steam"
        self._status = "Passive"
        self._attention_icon = ""
        self._icon_name = CFG["icon_name"]
        self._icon_path = CFG["icon_path"]
        self._last_click = 0.0
        self._menu_timeout = 0
        self._menu = SteamTrayMenu(bus)

    # --- signals (the panel listens for these to refresh the icon) ---
    @dbus.service.signal(SNI_IFACE, signature="")
    def NewIcon(self):
        pass

    @dbus.service.signal(SNI_IFACE, signature="")
    def NewTitle(self):
        pass

    @dbus.service.signal(SNI_IFACE, signature="")
    def NewAttentionIcon(self):
        pass

    @dbus.service.signal(SNI_IFACE, signature="")
    def NewToolTip(self):
        pass

    @dbus.service.signal(SNI_IFACE, signature="")
    def NewStatus(self):
        pass

    @dbus.service.signal(PROPS_IFACE, signature="sa{sv}as")
    def PropertiesChanged(
        self, interface_name, changed_properties, invalidated_properties
    ):
        pass

    # --- methods called by the panel host ---
    @dbus.service.method(SNI_IFACE, in_signature="ii", out_signature="")
    def Activate(self, x, y):
        now = time.monotonic()
        window = CFG["double_click_ms"] / 1000.0

        if now - self._last_click <= window:
            # second click of a double click -> open the Steam window
            self._last_click = 0.0
            self._cancel_pending_menu()
            log("double click -> opening Steam window")
            launch([CFG["window_url"]])
            return

        self._last_click = now
        log(f"single click (menu in {CFG['menu_delay_ms']:.0f} ms)")
        self._cancel_pending_menu()
        self._menu_timeout = GLib.timeout_add(CFG["menu_delay_ms"], self._open_menu)

    @dbus.service.method(SNI_IFACE, in_signature="ii", out_signature="")
    def SecondaryActivate(self, x, y):
        pass

    @dbus.service.method(SNI_IFACE, in_signature="is", out_signature="")
    def Scroll(self, delta, orientation):
        pass

    @dbus.service.method(SNI_IFACE, in_signature="ii", out_signature="")
    def ContextMenu(self, x, y):
        pass

    @dbus.service.method(SNI_IFACE, in_signature="s", out_signature="")
    def ProvideXdgActivationToken(self, token):
        pass

    # --- properties (dbus-python has no property support, so we implement
    #     org.freedesktop.DBus.Properties by hand) ---
    def _all_props(self):
        icon_path = self._icon_path if os.path.isdir(self._icon_path) else ""
        return {
            "Category": dbus.String("ApplicationStatus"),
            "Id": dbus.String(CFG["item_id"]),
            "Title": dbus.String(self._title),
            "Status": dbus.String(self._status),
            "WindowId": dbus.UInt32(0),
            "IconThemePath": dbus.String(icon_path),
            "IconName": dbus.String(self._icon_name),
            "IconPixmap": dbus.Array([], signature="(iiay)"),
            "OverlayIconName": dbus.String(""),
            "OverlayIconPixmap": dbus.Array([], signature="(iiay)"),
            "AttentionIconName": dbus.String(self._attention_icon),
            "AttentionIconPixmap": dbus.Array([], signature="(iiay)"),
            "ToolTip": dbus.Struct(
                (
                    dbus.String(self._icon_name),
                    dbus.Array([], signature="(iiay)"),
                    dbus.String(self._title),
                    dbus.String(self._description),
                ),
                signature="(sa(iiay)ss)",
            ),
            "Menu": dbus.ObjectPath(MENU_PATH),
            # False => the host calls Activate() on left click (that is what we
            # want).  Steam's own indicator effectively behaves as if this were
            # True, which is why the window never opens.
            "ItemIsMenu": dbus.Boolean(False),
        }

    @dbus.service.method(PROPS_IFACE, in_signature="ss", out_signature="v")
    def Get(self, interface_name, prop_name):
        props = self._all_props()
        if prop_name not in props:
            raise dbus.exceptions.DBusException(
                f"no such property '{prop_name}'",
                name="org.freedesktop.DBus.Error.UnknownProperty",
            )
        return props[prop_name]

    @dbus.service.method(PROPS_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface_name):
        return dbus.Dictionary(self._all_props(), signature="sv")

    @dbus.service.method(PROPS_IFACE, in_signature="ssv", out_signature="")
    def Set(self, interface_name, prop_name, value):
        raise dbus.exceptions.DBusException(
            f"property '{prop_name}' is read-only",
            name="org.freedesktop.DBus.Error.PropertyReadOnly",
        )

    # --- helpers ---
    def _cancel_pending_menu(self):
        if self._menu_timeout:
            GLib.source_remove(self._menu_timeout)
            self._menu_timeout = 0

    def _open_menu(self):
        self._menu_timeout = 0
        log("opening menu")
        dms_open_menu(CFG["item_id"])
        return False

    def set_state(self, title=None, description=None, status=None, attention=None):
        changed = {}
        if title is not None and title != self._title:
            self._title = title
            changed["Title"] = dbus.String(title)
            self.NewTitle()
        if description is not None and description != self._description:
            self._description = description
            changed["ToolTip"] = dbus.String(description)
            self.NewToolTip()
        if attention is not None and attention != self._attention_icon:
            self._attention_icon = attention
            changed["AttentionIconName"] = dbus.String(attention)
            self.NewAttentionIcon()
        if status is not None and status != self._status:
            self._status = status
            changed["Status"] = dbus.String(status)
            self.NewStatus()
        if changed:
            self.PropertiesChanged(
                SNI_IFACE,
                dbus.Dictionary(changed, signature="sv"),
                dbus.Array([], signature="s"),
            )

    def set_icon(self, name=None, path=None):
        changed = {}
        if name and name != self._icon_name:
            self._icon_name = name
            changed["IconName"] = dbus.String(name)
            self.NewIcon()
        if path and path != self._icon_path:
            self._icon_path = path
            changed["IconThemePath"] = dbus.String(path)
            self.NewIcon()
        if changed:
            self.PropertiesChanged(
                SNI_IFACE,
                dbus.Dictionary(changed, signature="sv"),
                dbus.Array([], signature="s"),
            )


class SteamMirror:
    """Mirrors tooltip/attention state, the icon and the menu from Steam."""

    def __init__(self, bus, item):
        self.bus = bus
        self.item = item
        self.steam_service = None
        self.steam_path = None

    @property
    def steam_address(self):
        """The address of Steam's indicator, as the watcher spells it."""
        if not self.steam_service or not self.steam_path:
            return None
        return self.steam_service + self.steam_path

    def reset(self):
        """Forget Steam's indicator (it is gone)."""
        if self.steam_service is None:
            return
        log("forgetting Steam's indicator")
        self.steam_service = None
        self.steam_path = None
        self.item._menu.set_remote(None, None)

    def find_steam_item(self, items):
        """Pick Steam's own indicator out of the watcher's item list."""
        for entry in items:
            service, _, path = str(entry).partition("/")
            if not path.startswith("/"):
                path = "/" + path
            if service == BUS_NAME:
                # That is us.
                continue
            try:
                obj = self.bus.get_object(service, path)
                item_props = dbus.Interface(obj, PROPS_IFACE)
                item_props.Get(
                    "org.kde.StatusNotifierItem",
                    "Id",
                    reply_handler=lambda iid, service=service, path=path: self._got_id(
                        str(iid), service, path
                    ),
                    error_handler=lambda e: None,
                )
            except dbus.DBusException as exc:
                log(f"could not read {service}{path}: {exc}")
                continue

    def _got_id(self, item_id, service, path):
        if item_id != "steam":
            return
        if self.steam_service == service and self.steam_path == path:
            return
        self.steam_service = service
        self.steam_path = path
        log(f"mirroring Steam indicator at {service}{path}")
        self._sync_steam_properties()
        try:
            self.bus.add_signal_receiver(
                self._on_properties_changed,
                dbus_interface=PROPS_IFACE,
                bus_name=service,
                path=path,
                path_keyword="object_path",
            )
        except dbus.DBusException as exc:
            log(f"could not subscribe to Steam properties: {exc}")

    def _sync_steam_properties(self):
        """Read Steam's title/menu/icon once and mirror them."""
        try:
            obj = self.bus.get_object(self.steam_service, self.steam_path)
            props = dbus.Interface(obj, PROPS_IFACE)
            all_props = props.GetAll("org.kde.StatusNotifierItem")
            menu_path = str(all_props.get("Menu", ""))
            if menu_path and not menu_path.startswith("/"):
                menu_path = "/" + menu_path
            self.item._menu.set_remote(self.steam_service, menu_path)
            title = all_props.get("Title")
            status = all_props.get("Status")
            icon_name = all_props.get("IconName")
            icon_path = all_props.get("IconThemePath")
            self.item.set_icon(
                name=str(icon_name) if icon_name else None,
                path=str(icon_path) if icon_path else None,
            )
            self.item.set_state(
                title=str(title) if title is not None else None,
                status=str(status) if status is not None else None,
            )
        except dbus.DBusException as exc:
            log(f"could not read Steam properties: {exc}")

    def _on_properties_changed(self, interface, changed, invalidated, object_path=None):
        if not changed:
            return
        title = changed.get("Title")
        tooltip = changed.get("ToolTip")
        status = changed.get("Status")
        attention = changed.get("AttentionIconName")
        description = None
        if tooltip is not None:
            try:
                description = str(tooltip[3])
            except (IndexError, TypeError, ValueError):
                description = None
        self.item.set_state(
            title=str(title) if title is not None else None,
            description=description,
            status=str(status) if status is not None else None,
            attention=str(attention) if attention is not None else None,
        )


class TrayPresence:
    """Controls whether our icon is in the panel's tray.

    The watcher spec has no "unregister" call: the watcher drops an item
    when the bus name it was registered under disappears.  So the item is
    registered under a well-known name of our own - releasing that name
    makes the panel drop the icon, and taking the name again brings the
    icon back.
    """

    def __init__(self, bus):
        self.bus = bus
        # Do we own the bus name the item is registered under?
        self.owned = False
        # Have we already complained about not getting the name?
        self.complained = False

    def _watcher(self):
        return dbus.Interface(
            self.bus.get_object(WATCHER_NAME, WATCHER_PATH), WATCHER_IFACE
        )

    def items(self):
        """The items the panel's watcher knows about (None if it is gone)."""
        try:
            props = dbus.Interface(
                self.bus.get_object(WATCHER_NAME, WATCHER_PATH), PROPS_IFACE
            )
            return [
                str(i)
                for i in props.Get(WATCHER_IFACE, "RegisteredStatusNotifierItems")
            ]
        except dbus.DBusException as exc:
            log(f"watcher unavailable ({exc}), will retry")
            return None

    def acquire(self):
        """Take the bus name the item is registered under."""
        if self.owned:
            return True
        reply = self.bus.request_name(BUS_NAME, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)
        if reply not in (
            dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER,
            dbus.bus.REQUEST_NAME_REPLY_ALREADY_OWNER,
        ):
            if not self.complained:
                log(f"could not own {BUS_NAME} (reply {reply})")
                self.complained = True
            return False
        self.owned = True
        self.complained = False
        return True

    def release(self):
        """Give the bus name up: the watcher drops the item with it."""
        if not self.owned:
            return
        self.bus.release_name(BUS_NAME)
        self.owned = False

    def register(self):
        """Ask the watcher to show our item."""
        try:
            self._watcher().RegisterStatusNotifierItem(BUS_NAME)
            log("registered with the StatusNotifierWatcher")
        except dbus.DBusException as exc:
            log(f"could not register with the watcher: {exc}")


def sync_tray(item, mirror, presence):
    """Keep the tray in sync with the Steam client.

    The icon is only in the tray while Steam runs: it is registered with
    the panel's watcher when Steam comes up and taken out of it again when
    Steam goes away.
    """
    reap_children()

    items = presence.items()
    listed = items is not None and QUALIFIED_ITEM in items

    # Steam's own indicator is the most reliable sign that Steam is up.
    steam_gone = (
        mirror.steam_address and items is not None and mirror.steam_address not in items
    )
    if steam_gone:
        mirror.reset()

    running = steam_running() or mirror.steam_service is not None

    if not running and presence.owned:
        log("Steam is gone, taking the icon out of the tray")
        presence.release()
    elif running and items is not None and not listed and presence.acquire():
        # The watcher does not know us: either we are just coming back from
        # Steam being closed, or the shell restarted and lost our item.
        presence.register()

    if items is not None:
        mirror.find_steam_item(items)

    item.set_state(status="Active" if running else "Passive")
    return True


def main():
    bus = dbus.SessionBus()

    item = SteamTrayItem(bus)
    mirror = SteamMirror(bus, item)
    presence = TrayPresence(bus)

    GLib.timeout_add_seconds(2, lambda: sync_tray(item, mirror, presence))

    log("running")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
