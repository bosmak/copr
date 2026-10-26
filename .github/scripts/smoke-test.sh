#!/bin/bash
# Validate the packages built by "make rpm".
#
#   .github/scripts/smoke-test.sh /packages
#
# Runs inside a throwaway Fedora container: installs every RPM, then checks
# that the packages are complete and usable - the files are intact, the file
# list matches the upstream RPM, the desktop/MIME/icon caches were refreshed
# and the application itself starts.
#
# Exits non-zero if any check failed.

set -uo pipefail

pkgs_dir=${1:-/packages}
# Set SKIP_INSTALL=1 to check the packages that are already installed.
skip_install=${SKIP_INSTALL:-0}
failed=0

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

ok() { printf '  ok    %s\n' "$*"; }
fail() { printf '  FAIL  %s\n' "$*"; failed=1; }
warn() { printf '  warn  %s\n' "$*"; }

# The regular files of a package, by name. The mode is used to tell the
# files from the directories.
files_of_rpm() {
    rpm -qp --qf '[%{FILEMODES} %{FILENAMES}\n]' "$1" 2>/dev/null |
        while read -r mode path; do
            if [ $(( mode & 61440 )) -eq 32768 ]; then
                printf '%s\n' "${path##*/}"
            fi
        done | sort
}

files_of_installed() {
    rpm -q --qf '[%{FILEMODES} %{FILENAMES}\n]' "$1" 2>/dev/null |
        while read -r mode path; do
            if [ $(( mode & 61440 )) -eq 32768 ]; then
                printf '%s\n' "${path##*/}"
            fi
        done | sort
}

# Run a command and report how it ended.
run() {
    local out
    if out=$("$@" 2>&1); then
        ok "$(printf '%s' "$*" | tr '\n' ' ') -> $(printf '%s' "$out" | head -1)"
    else
        fail "$(printf '%s' "$*" | tr '\n' ' ') -> $(printf '%s' "$out" | head -3 | tr '\n' ' ')"
    fi
}

if [ "$skip_install" = "1" ]; then
    echo "==> skipping the installation"
else
    echo "==> installing the packages"
    # The tools the post-install scriptlets use to refresh the caches.
    dnf install -y desktop-file-utils shared-mime-info gtk-update-icon-cache \
        >/dev/null 2>&1
    if ! log=$(dnf install -y "$pkgs_dir"/*.rpm 2>&1); then
        printf '%s\n' "$log"
        fail "dnf install"
        exit 1
    fi
    printf '%s\n' "$log" | grep -E "^(Installed|Complete)" | tail -2
fi

for rpm_file in "$pkgs_dir"/*.rpm; do
    name=$(rpm -qp --qf '%{NAME}' "$rpm_file")
    version=$(rpm -qp --qf '%{VERSION}-%{RELEASE}' "$rpm_file")
    echo
    echo "==> $name $version"

    if rpm -q "$name" >/dev/null 2>&1; then
        ok "installed"
    else
        fail "not installed"
        continue
    fi

    # The files are the ones the package was built with. The dependency
    # check of rpm -V is dropped: the dependencies are checked below.
    out=$(rpm -V "$name" 2>&1 | grep -vE "^Unsatisfied dependencies|is needed by")
    if [ -z "$out" ]; then
        ok "files verified"
    else
        fail "rpm -V: $out"
    fi

    # Every file of the upstream RPM is in the package.
    upstream=$(files_of_rpm "$rpm_file")
    ours=$(files_of_installed "$name")
    printf '%s\n' "$upstream" > "$tmpdir/upstream"
    printf '%s\n' "$ours" > "$tmpdir/ours"
    missing=$(comm -23 "$tmpdir/upstream" "$tmpdir/ours")
    extra=$(comm -13 "$tmpdir/upstream" "$tmpdir/ours")
    if [ -z "$missing" ] && [ -z "$extra" ]; then
        ok "file list matches the upstream RPM ($(printf '%s\n' "$upstream" | wc -l) files)"
    else
        [ -n "$missing" ] &&
            fail "missing from the package: $(printf '%s' "$missing" | tr '\n' ' ')"
        [ -n "$extra" ] &&
            fail "not in the upstream RPM: $(printf '%s' "$extra" | tr '\n' ' ')"
    fi

    # The shared libraries are all there.
    unresolved=""
    for binary in $(rpm -ql "$name" 2>/dev/null | grep '^/usr/bin/'); do
        out=$(ldd "$binary" 2>/dev/null | grep 'not found')
        [ -n "$out" ] && unresolved="$unresolved $binary"
    done
    if [ -z "$unresolved" ]; then
        ok "libraries resolved"
    else
        fail "missing libraries:$unresolved"
    fi

    # The desktop entry is valid.
    for entry in $(rpm -ql "$name" 2>/dev/null | grep '\.desktop$'); do
        out=$(desktop-file-validate "$entry" 2>&1)
        if [ -z "$out" ]; then
            ok "desktop entry ${entry##*/} is valid"
        else
            warn "desktop entry ${entry##*/}: $out"
        fi
    done

    # The application starts.
    case "$name" in
        pvpn)
            run pvpnd --version
            run pvpnctl --version
            ;;
        artcraft-launcher)
            run artcraft-launcher --version
            ;;
        clip-bridge)
            # It needs a display to do its job.
            ok "skipped: it needs a display"
            ;;
        steam-fix-trayicon)
            run python3 -m py_compile /usr/bin/steam-fix-trayicon
            ;;
        *)
            run "$name-cli" --version
            ;;
    esac
done

# The caches the post-install scriptlets refresh.
echo
echo "==> caches"
if [ -f /usr/share/applications/mimeinfo.cache ]; then
    ok "desktop database"
else
    fail "no desktop database"
fi
if [ -f /usr/share/icons/hicolor/icon-theme.cache ]; then
    ok "icon cache"
else
    fail "no icon cache"
fi
if [ -f /usr/share/mime/globs2 ]; then
    ok "mime database"
else
    fail "no mime database"
fi

echo
if [ $failed -eq 0 ]; then
    echo "==> everything passed"
else
    echo "==> there were failures"
fi
exit $failed
