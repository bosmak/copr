%global debug_package %{nil}

Name:           clip-bridge
Version:        0.1.9
Release:        1%{?dist}
Summary:        Sync your X11 and Wayland clipboard seamlessly
License:        MIT
URL:            https://github.com/noctisynth/clip-bridge
Source0:        https://github.com/noctisynth/clip-bridge/archive/refs/tags/clip-bridge-v%{version}.tar.gz#/clip-bridge-v%{version}.tar.gz
# Vendored Rust crates. Copr's mock chroot has --resolv-conf=off and
# can't reach crates.io, so we ship the deps and build offline.
# Regenerate with 'cargo vendor' whenever upstream's Cargo.lock changes.
Source1:        clip-bridge-vendor.tar.xz
Source2:        clip-bridge.service

BuildRequires:  cargo
BuildRequires:  rust
BuildRequires:  systemd-rpm-macros
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-protocols)
BuildRequires:  pkgconfig(xkbcommon)

Requires:      wayland-client
Requires:      libx11
Requires:      libxkbcommon
Recommends:    wl-clipboard
Recommends:    xclip

ExclusiveArch:  x86_64

%description
clip-bridge synchronizes the X11 and Wayland clipboards seamlessly. Run
it once and copying in one environment pastes in the other — copy from
X11, paste into Wayland; copy from Wayland, paste into X11.

%prep
# Tag prefix is 'clip-bridge-v…', so the upstream tarball extracts to
# 'clip-bridge-clip-bridge-v%{version}/'.
%autosetup -n clip-bridge-clip-bridge-v%{version}
tar -xf %{SOURCE1}

# Tell cargo to use the vendored sources from ./vendor/ — required for
# '--offline' builds in a network-less mock chroot.
mkdir -p .cargo
cat > .cargo/config.toml <<'CFG'
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"
CFG

%build
export CARGO_HOME=%{_builddir}/cargo-home
cargo build --release --offline --locked

%install
install -Dm755 target/release/clip-bridge %{buildroot}%{_bindir}/clip-bridge
install -Dm644 %{SOURCE2} %{buildroot}/usr/lib/systemd/user/clip-bridge.service

install -Dm644 LICENSE %{buildroot}%{_licensedir}/clip-bridge/LICENSE

%files
%license %{_licensedir}/clip-bridge/LICENSE
%{_bindir}/clip-bridge
/usr/lib/systemd/user/clip-bridge.service

%changelog
* Thu Oct 16 2025 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.1.9-1
- initial COPR package
