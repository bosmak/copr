%global debug_package %{nil}
# Upstream ships fully-static, already-stripped Go binaries. Re-running
# strip on them would mutate ELF section metadata and diverge from
# upstream's released bytes; disabling it keeps the shipped binary
# bit-identical to the GitHub release.
%global __strip /bin/true

%global with_killswitch 1
%global pvpn_dirs /etc/pvpn /var/lib/pvpn

Name:           pvpn
Version:        0.2.10
Release:        1%{?dist}
Summary:        Proton VPN client with TUI for Linux (WireGuard + Stealth)
License:        GPL-3.0-or-later
URL:            https://github.com/YourDoritos/pVPN
# Prebuilt amd64 binaries from the upstream release. These are static
# Go binaries, so no .so runtime deps are needed.
Source0:        https://github.com/YourDoritos/pVPN/releases/download/v%{version}/pvpnd-linux-amd64
Source1:        https://github.com/YourDoritos/pVPN/releases/download/v%{version}/pvpn-linux-amd64
Source2:        https://github.com/YourDoritos/pVPN/releases/download/v%{version}/pvpnctl-linux-amd64
# Upstream's SHA256SUMS, used in the prep section to verify Source0–2.
Source3:        https://github.com/YourDoritos/pVPN/releases/download/v%{version}/SHA256SUMS
# Upstream's systemd unit files and LICENSE, pulled directly from the
# matching tag on GitHub. Tracking these as URLs (not as vendored files
# in this repo) means we always follow upstream without manual updates.
Source4:        https://raw.githubusercontent.com/YourDoritos/pVPN/v%{version}/dist/pvpnd.service
Source5:        https://raw.githubusercontent.com/YourDoritos/pVPN/v%{version}/dist/pvpn-preboot-killswitch.service
Source6:        https://raw.githubusercontent.com/YourDoritos/pVPN/v%{version}/dist/systemd-time-wait-sync-pvpn-override.conf
Source7:        https://raw.githubusercontent.com/YourDoritos/pVPN/v%{version}/LICENSE
# This one is *our* config (not upstream's) — a sysusers drop-in that
# creates the 'pvpn' system group. Kept as a vendored file in the repo.
Source8:        pvpn.sysusers.conf

# Needed for the systemd path and scriptlet macros.
BuildRequires:  systemd-rpm-macros

Requires:       nftables
Requires:       systemd
Requires:       (kernel >= 5.6 or kmod-wireguard)
Recommends:     google-noto-emoji-fonts

# pVPN binaries are x86_64 only.
ExclusiveArch:  x86_64

%description
A fast, lightweight Proton VPN client for Linux with a terminal user
interface. Daemon-based architecture: the VPN connection persists after
the TUI is closed. Written in Go.

Unlike Proton's official Linux client, pVPN:
 * Does not require NetworkManager (auto-detects systemd-networkd,
   iwd, dhcpcd, or bare setups).
 * Supports the Stealth protocol (WireGuard-over-TLS) to bypass
   DPI / firewalls.
 * Runs as a small Go daemon plus a TUI — no Electron, no Python.

The daemon runs as root (with CAP_NET_ADMIN) and manages the
WireGuard interface, routes, nftables kill switch, and Proton
session. The TUI and pvpnctl run unprivileged and talk to the daemon
over a Unix socket guarded by the 'pvpn' system group.

%prep
# Verify the prebuilt binaries against upstream's SHA256SUMS, restricted
# to the files we actually ship (amd64 only).
for f in %{SOURCE0} %{SOURCE1} %{SOURCE2}; do
    bn=$(basename "$f")
    expected=$(awk -v f="$bn" '$2 == f {print $1}' %{SOURCE3})
    actual=$(sha256sum "$f" | awk '{print $1}')
    if [ "$expected" != "$actual" ]; then
        echo "SHA256 mismatch for $bn: expected $expected, got $actual" >&2
        exit 1
    fi
done

# No extraction step needed — the binaries and other files are
# referenced directly by their individual SourceN entries in install.

%build
# Nothing to build — we ship upstream's prebuilt binaries verbatim.

%install
install -Dm755 %{SOURCE0} %{buildroot}%{_bindir}/pvpnd
install -Dm755 %{SOURCE1} %{buildroot}%{_bindir}/pvpn
install -Dm755 %{SOURCE2} %{buildroot}%{_bindir}/pvpnctl

# The vendored pvpnd.service ships with ExecStart=/usr/local/bin/pvpnd
# (the path upstream's install.sh uses); rewrite it to the Fedora bindir
# macro so the unit doesn't pin a distro-specific path.
sed 's|^ExecStart=.*|ExecStart=%{_bindir}/pvpnd|' \
    %{SOURCE4} \
    | install -Dm644 /dev/stdin %{buildroot}%{_unitdir}/pvpnd.service

%if %{with_killswitch}
install -Dm644 %{SOURCE5} %{buildroot}%{_unitdir}/pvpn-preboot-killswitch.service
install -Dm644 %{SOURCE6} %{buildroot}%{_unitdir}/systemd-time-wait-sync.service.d/10-pvpn.conf
%endif

install -Dm644 %{SOURCE7} %{buildroot}%{_licensedir}/pvpn/LICENSE

install -Dm644 %{SOURCE8} %{buildroot}%{_sysusersdir}/pvpn.conf

%post
%systemd_post pvpnd.service

%if %{with_killswitch}
%systemd_enable pvpnd-preboot-killswitch.service
%endif

for d in %{pvpn_dirs}; do
    [ -d "$d" ] || install -dm750 -o root -g pvpn "$d"
done

cat <<'EOF'

pVPN %{version} installed.

Two manual steps are needed before the client can talk to the daemon:

  1. Add your user to the 'pvpn' system group, then log out
     and back in (or run 'newgrp pvpn' in the current shell):

       sudo usermod -aG pvpn $USER

  2. The 'pvpnd' service is enabled and will start at boot.
     To start it now without rebooting:

       sudo systemctl start pvpnd

Then launch the TUI with 'pvpn', or query the daemon with
'pvpnctl status'.

Config: /etc/pvpn/   State: /var/lib/pvpn/
EOF

%preun
%systemd_preun pvpnd.service

%postun
%systemd_postun pvpnd.service
%if %{with_killswitch}
%systemd_postun pvpnd-preboot-killswitch.service
%endif

%files
%license %{_licensedir}/pvpn/LICENSE
%{_bindir}/pvpn
%{_bindir}/pvpnd
%{_bindir}/pvpnctl
%{_unitdir}/pvpnd.service
%if %{with_killswitch}
%{_unitdir}/pvpn-preboot-killswitch.service
%{_unitdir}/systemd-time-wait-sync.service.d/10-pvpn.conf
%endif
%{_sysusersdir}/pvpn.conf

%changelog
* Thu Oct 16 2025 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.2.10-1
- initial COPR package
