%global debug_package %{nil}
# Upstream ships a stripped binary; re-running strip on it would mutate
# ELF section metadata and diverge from upstream's released bytes.
%global __strip /bin/true

Name:           clip-bridge
Version:        0.1.9
Release:        1%{?dist}
Summary:        Sync your X11 and Wayland clipboard seamlessly
License:        MIT
URL:            https://github.com/noctisynth/clip-bridge
# Upstream ships a prebuilt x86_64 binary in their GitHub release. Its
# only dynamic deps are glibc / libm / libgcc — the X11 and Wayland
# protocol code is pure Rust, so it has no .so Requires on libX11 /
# libwayland-client. We just repackage it as-is.
Source0:        https://github.com/noctisynth/clip-bridge/releases/download/clip-bridge-v%{version}/clip-bridge-%{version}-x86_64.tar.gz
Source1:        clip-bridge.service

# Needed for the systemd_user_post / preun / postun macros.
BuildRequires:  systemd-rpm-macros

# wl-clipboard and xclip are still needed for actual clipboard I/O on
# the Wayland and X11 sides respectively — the binary bridges selection
# events between them.
Recommends:     wl-clipboard
Recommends:     xclip

ExclusiveArch:  x86_64

%description
clip-bridge synchronizes the X11 and Wayland clipboards seamlessly. Run
it once and copying in one environment pastes in the other — copy from
X11, paste into Wayland; copy from Wayland, paste into X11.

%prep
# The release tarball ships the binary and LICENSE at the root, with no
# enclosing directory. autosetup -c creates the build dir first so the
# files land inside it.
%autosetup -c -n clip-bridge-%{version}

%build
# Nothing to build — we ship the upstream prebuilt binary verbatim.

%install
install -Dm755 clip-bridge %{buildroot}%{_bindir}/clip-bridge
install -Dm644 %{SOURCE1} %{buildroot}/usr/lib/systemd/user/clip-bridge.service
install -Dm644 LICENSE %{buildroot}%{_licensedir}/clip-bridge/LICENSE

%post
# Best-effort auto-enable for the installing user's session. If they
# don't have an active session (e.g. installing inside a container or
# over SSH without linger), this is a no-op and the post-install
# message below tells them how to enable it manually.
%systemd_user_post clip-bridge.service

# Verify the auto-enable actually worked. The check itself needs an
# active user session (XDG_RUNTIME_DIR), so in mock / kickstart /
# non-interactive installs it will report "not enabled" — that's
# expected, not a failure.
if [ -n "${XDG_RUNTIME_DIR:-}" ] && [ -x /usr/bin/systemctl ] \
   && /usr/bin/systemctl --user is-enabled clip-bridge.service >/dev/null 2>&1; then
    status='enabled — will auto-start on your next login'
else
    status='NOT auto-enabled (no active user session; run the commands below)'
fi

cat <<EOF

================================================================
 clip-bridge %{version} — USER service, not a system service!
================================================================

  Use:  systemctl --user status clip-bridge.service
  Not:  systemctl       status clip-bridge.service   <- won't find it

  Status: $status

  To enable and start it manually (if not already done):

         systemctl --user enable --now clip-bridge.service

  Or just run the binary once to try it (no auto-start):

         clip-bridge

  Verify with:   systemctl --user status clip-bridge.service
================================================================
EOF

%preun
%systemd_user_preun clip-bridge.service

%postun
%systemd_user_postun clip-bridge.service

%files
%license %{_licensedir}/clip-bridge/LICENSE
%{_bindir}/clip-bridge
/usr/lib/systemd/user/clip-bridge.service

%changelog
* Thu Oct 16 2025 Gustavo Bosmak <gustavo.bosmak@gmail.com> - 0.1.9-1
- initial COPR package
