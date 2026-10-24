#!/usr/bin/env python3
"""Replacement Steam tray icon (StatusNotifierItem).

    single click  ->  Steam's own menu (proxied from Steam's dbusmenu)
    double click  ->  opens / focuses the Steam window
    right click   ->  same menu

Steam's Linux tray icon is a libappindicator item, so the panel always
answers a click with Steam's popup menu and the window can never be opened
from the tray - https://github.com/ValveSoftware/steam-for-linux/issues/3519

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

ITEM_PATH = "/StatusNotifierItem"
MENU_PATH = "/MenuBar"
BUS_NAME = "org.kde.StatusNotifierItem-steam-window"

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
    print("[steam-fix-trayicon] %s" % msg, file=sys.stderr, flush=True)


def steam_running():
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open("/proc/%s/comm" % pid) as fh:
                name = fh.read().strip()
        except OSError:
            continue
        if name in ("steam", "steamwebhelper"):
            return True
    return False


def launch(args):
    """Run a steam CLI command without blocking the main loop."""
    cmd = [CFG["steam_bin"]] + list(args)
    log("launching: %s" % " ".join(cmd))
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        log("failed to launch %s: %s" % (cmd[0], exc))


def dms_instances():
    """Ids of the running quickshell instances that host the DMS shell."""
    try:
        out = subprocess.run(
            ["quickshell", "list", "--all"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).stdout.decode(errors="replace")
    except Exception:
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
            )
        except Exception:
            continue
        if b"SUCCESS" in res.stdout:
            return True
    log("could not ask DMS to open the menu for %s" % item_id)
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
            log("menu proxied to %s%s" % (service, path))
        except Exception as exc:
            self._remote = None
            log("could not proxy menu: %s" % exc)

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
                return self._remote.GetLayout(parent_id, recursion_depth, property_names)
            except Exception as exc:
                log("GetLayout proxy failed: %s" % exc)
        return dbus.UInt32(1), self._fallback_layout()

    @dbus.service.method(MENU_IFACE, in_signature="asas", out_signature="a{ia{sv}}")
    def GetGroupProperties(self, ids, property_names):
        if self._remote is not None:
            try:
                return self._remote.GetGroupProperties(ids, property_names)
            except Exception as exc:
                log("GetGroupProperties proxy failed: %s" % exc)
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
            except Exception:
                pass
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
            except Exception as exc:
                log("Event proxy failed: %s" % exc)
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
            except Exception:
                pass
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
    def PropertiesChanged(self, interface_name, changed_properties, invalidated_properties):
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
        log("single click (menu in %.0f ms)" % CFG["menu_delay_ms"])
        self._cancel_pending_menu()
        self._menu_timeout = GLib.timeout_add(
            CFG["menu_delay_ms"], self._open_menu
        )

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
                "no such property '%s'" % prop_name,
                name="org.freedesktop.DBus.Error.UnknownProperty",
            )
        return props[prop_name]

    @dbus.service.method(PROPS_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface_name):
        return dbus.Dictionary(self._all_props(), signature="sv")

    @dbus.service.method(PROPS_IFACE, in_signature="ssv", out_signature="")
    def Set(self, interface_name, prop_name, value):
        raise dbus.exceptions.DBusException(
            "property '%s' is read-only" % prop_name,
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

    def find_steam_item(self):
        try:
            watcher = self.bus.get_object(
                "org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher"
            )
            watcher_props = dbus.Interface(watcher, PROPS_IFACE)
            watcher_props.Get(
                "org.kde.StatusNotifierWatcher",
                "RegisteredStatusNotifierItems",
                reply_handler=lambda items: self._check_items(items),
                error_handler=lambda e: log("watcher error: %s" % e),
            )
        except Exception as exc:
            log("could not query watcher: %s" % exc)

    def _check_items(self, items):
        for entry in items:
            service, _, path = str(entry).partition("/")
            if not path.startswith("/"):
                path = "/" + path
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
            except Exception:
                continue

    def _got_id(self, item_id, service, path):
        if item_id != "steam":
            return
        if self.steam_service == service and self.steam_path == path:
            return
        self.steam_service = service
        self.steam_path = path
        log("mirroring Steam indicator at %s%s" % (service, path))
        self._sync_steam_properties()
        try:
            self.bus.add_signal_receiver(
                self._on_properties_changed,
                dbus_interface=PROPS_IFACE,
                bus_name=service,
                path=path,
                path_keyword="object_path",
            )
        except Exception as exc:
            log("could not subscribe to Steam properties: %s" % exc)

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
        except Exception as exc:
            log("could not read Steam properties: %s" % exc)

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
            except Exception:
                description = None
        self.item.set_state(
            title=str(title) if title is not None else None,
            description=description,
            status=str(status) if status is not None else None,
            attention=str(attention) if attention is not None else None,
        )


def sync_with_watcher(bus, item, mirror):
    """Make sure we stay registered.

    The panel's StatusNotifierWatcher belongs to the shell process, so it
    disappears (and forgets us) whenever the shell restarts.  Re-register
    whenever we are missing from its item list.
    """
    try:
        watcher = bus.get_object("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher")
        watcher_props = dbus.Interface(watcher, PROPS_IFACE)
        items = [
            str(i)
            for i in watcher_props.Get(
                "org.kde.StatusNotifierWatcher", "RegisteredStatusNotifierItems"
            )
        ]
        if bus.get_unique_name() + ITEM_PATH not in items:
            watcher.RegisterStatusNotifierItem(ITEM_PATH)
            log("registered with StatusNotifierWatcher")
    except Exception as exc:
        log("watcher unavailable (%s), will retry" % exc)
    mirror.find_steam_item()
    return True


def poll_steam_state(item):
    """Keep Status in sync with whether Steam is running."""
    running = steam_running()
    item.set_state(status="Active" if running else "Passive")
    return True


def main():
    bus = dbus.SessionBus()
    try:
        dbus.service.BusName(BUS_NAME, bus)
    except Exception as exc:
        log("could not own bus name: %s" % exc)

    item = SteamTrayItem(bus)
    item.set_state(status="Active" if steam_running() else "Passive")

    mirror = SteamMirror(bus, item)
    GLib.timeout_add_seconds(5, lambda: poll_steam_state(item))
    GLib.timeout_add_seconds(3, lambda: sync_with_watcher(bus, item, mirror))

    log("running")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
