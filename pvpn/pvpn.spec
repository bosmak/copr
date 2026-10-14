%global go_minimum 1.21
%global with_killswitch 1
%global pvpn_dirs /etc/pvpn /var/lib/pvpn
%global debug_package %{nil}

Name:           pvpn
Version:        0.2.10
Release:        1%{?dist}
Summary:        Proton VPN client with TUI for Linux (WireGuard + Stealth)
License:        GPL-3.0-or-later
URL:            https://github.com/YourDoritos/pVPN
Source0:        https://github.com/YourDoritos/pVPN/archive/v%{version}.tar.gz#/pVPN-%{version}.tar.gz
# Vendored Go modules. COPR's mock chroot has --resolv-conf=off and
# can't reach proxy.golang.org, so we ship the deps and build with
# -mod=vendor + GOPROXY=off. Regenerate with `go mod vendor` whenever
# the upstream go.mod changes, then update this file via the workflow.
Source1:        pvpn-vendor.tar.xz

BuildRequires:  golang >= %{go_minimum}
BuildRequires:  systemd-rpm-macros

# pVPN binaries are Go-built, statically linked; x86_64 only.
ExclusiveArch:  x86_64

Requires:       nftables
Requires:       systemd
Requires:       (kernel >= 5.6 or kmod-wireguard)
Recommends:     google-noto-emoji-fonts

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
%autosetup -n pVPN-%{version}
tar -xf %{SOURCE1}

%build
export GOPATH=%{_builddir}/gopath
export GOCACHE=%{_builddir}/cache
export GOPROXY=off
export GOFLAGS="-buildmode=pie -trimpath -modcacherw -mod=vendor"

ldflags="-s -w -X main.version=%{version}"

go build -ldflags "$ldflags" -o pvpnd   ./cmd/pvpnd
go build -ldflags "$ldflags" -o pvpn    ./cmd/pvpn
go build -ldflags "$ldflags" -o pvpnctl ./cmd/pvpnctl

%install
install -Dm755 pvpnd   %{buildroot}%{_bindir}/pvpnd
install -Dm755 pvpn    %{buildroot}%{_bindir}/pvpn
install -Dm755 pvpnctl %{buildroot}%{_bindir}/pvpnctl

sed 's|^ExecStart=.*|ExecStart=%{_bindir}/pvpnd|' \
    dist/pvpnd.service \
    | install -Dm644 /dev/stdin %{buildroot}%{_unitdir}/pvpnd.service

%if %{with_killswitch}
install -Dm644 dist/pvpn-preboot-killswitch.service \
    %{buildroot}%{_unitdir}/pvpn-preboot-killswitch.service
install -Dm644 dist/systemd-time-wait-sync-pvpn-override.conf \
    %{buildroot}%{_unitdir}/systemd-time-wait-sync.service.d/10-pvpn.conf
%endif

mkdir -p %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/pvpn.conf <<'SYSEOF'
g pvpn - "pVPN system group"
SYSEOF
chmod 0644 %{buildroot}%{_sysusersdir}/pvpn.conf

install -Dm644 LICENSE \
    %{buildroot}%{_licensedir}/pvpn/LICENSE

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
  sudo usermod -aG pvpn $USER   # then newgrp or log out / in
  pvpn                          # TUI
  pvpnctl status                # CLI

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
