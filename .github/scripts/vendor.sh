#!/bin/bash
# Vendor the dependencies of a source package into a tarball.
#
#   .github/scripts/vendor.sh <package-dir> <sources-dir>
#
# Go and Rust projects download their dependencies while they are built.
# To make the build itself work without the network, the dependencies are
# vendored into a tarball that is shipped next to the sources:
#
#   <package-dir>-vendor.tar.xz
#
# The tarball holds a "vendor" directory, which is what the specs of the
# packages expect (the cargo_prep macro of cargo-rpm-macros points cargo
# at it). A package with a web frontend also gets its built assets, and a
# package that needs a patched crate gets that crate under "patched".
#
# The source of the package is downloaded when it is not in the sources
# directory yet. The vendoring is done with the toolchain of the host; if
# there is none, a throwaway container is used instead.

set -euo pipefail

pkg_dir=${1:?the package directory is required}
sources_dir=${2:?the sources directory is required}

# The image of the container that does the vendoring when the host has no
# toolchain for it.
image=${VENDOR_IMAGE:-fedora:44}

specs=("$pkg_dir"/*.spec)
if [ ! -f "${specs[0]}" ]; then
    echo "error: no spec in $pkg_dir" >&2
    exit 1
fi
spec=${specs[0]}
version=$(grep -m1 '^Version:' "$spec" | awk '{print $2}')
pkg=$(basename "$pkg_dir")
vendor_tar="$sources_dir/$pkg-vendor.tar.xz"

# The upstream source of the package.
src0=$(awk '/^Source0:/{$1=""; sub(/^[ \t]+/,""); print; exit}' "$spec")
src0=${src0//%\{version\}/$version}
commit=$(awk '/^%global commit /{print $3; exit}' "$spec")
[ -n "$commit" ] && src0=${src0//%\{commit\}/$commit}
src0_name=$(basename "${src0%%#*}")
[[ "$src0" == *#/* ]] && src0_name="${src0#*#/}"
src0_file="$sources_dir/$src0_name"

# Only the source tarballs of the Go and Rust projects have dependencies
# to vendor. The other packages ship a binary or a file that is part of
# the repository.
case "$src0" in
    http://* | https://*) ;;
    *)
        echo "==> $pkg has no upstream source, nothing to vendor"
        exit 0
        ;;
esac

case "$src0_name" in
    *.tar | *.tar.* | *.tgz | *.tbz2 | *.txz) ;;
    *)
        echo "==> the source of $pkg is not a tarball, nothing to vendor"
        exit 0
        ;;
esac

if [ ! -f "$src0_file" ]; then
    echo "==> fetching $src0"
    curl -fsSL "$src0" -o "$src0_file"
fi

work=$(mktemp -d --tmpdir "copr-vendor-XXXXXX")
trap 'rm -rf "$work"' EXIT

tar -xf "$src0_file" -C "$work" --strip-components=1

tool=""
packages=""
if [ -f "$work/go.mod" ]; then
    echo "==> vendoring the Go modules of $pkg"
    tool=go
    packages=golang
elif [ -f "$work/Cargo.toml" ]; then
    echo "==> vendoring the Rust crates of $pkg"
    tool=cargo
    packages=cargo
else
    echo "==> $pkg has no dependencies to vendor"
    exit 0
fi

has_frontend=0
if [ -f "$work/ui/pnpm-lock.yaml" ]; then
    echo "==> building the frontend of $pkg"
    has_frontend=1
    packages="$packages pnpm"
fi

missing_tool=0
if ! command -v "$tool" >/dev/null 2>&1; then
    missing_tool=1
fi
if [ "$has_frontend" -eq 1 ] \
   && ! command -v pnpm >/dev/null 2>&1; then
    missing_tool=1
fi

if [ "$missing_tool" -eq 0 ]; then
    case $tool in
        go)
            (cd "$work" && go mod download && go mod vendor)
            ;;
        cargo)
            (cd "$work" && cargo vendor --locked vendor >/dev/null)
            ;;
    esac
    if [ "$has_frontend" -eq 1 ]; then
        (cd "$work/ui" \
            && pnpm install --frozen-lockfile \
            && pnpm run build)
    fi
else
    container=$(command -v podman 2>/dev/null || command -v docker 2>/dev/null || true)
    if [ -z "$container" ]; then
        echo "error: $tool is needed to vendor the dependencies of $pkg" >&2
        [ "$has_frontend" -eq 1 ] && \
            echo "       pnpm is needed to build its frontend" >&2
        echo "       (install it, or install podman or docker)" >&2
        exit 1
    fi
    echo "==> a required tool is missing on the host, using the $image container"
    "$container" run --rm \
        -v "$work:/work:Z" \
        "$image" \
        bash -c "
            set -euo pipefail
            dnf install -y $packages
            cd /work
            $([ "$tool" = go ] \
                && echo 'go mod download && go mod vendor' \
                || echo 'cargo vendor --locked vendor >/dev/null')
            $([ "$has_frontend" -eq 1 ] \
                && echo 'cd ui && pnpm install --frozen-lockfile && pnpm run build')
        "
fi

# A crate whose build script needs a local input can be patched without
# invalidating the checksums of the original vendored crate. The patched
# copy is selected by a [patch.crates-io] entry in the package's spec.
if compgen -G "$pkg_dir/vendor-patches/*.patch" >/dev/null; then
    command -v patch >/dev/null 2>&1 || {
        echo "error: patch is needed to prepare the vendored crates" >&2
        exit 1
    }
    mkdir -p "$work/patched"
    for patch_file in "$pkg_dir"/vendor-patches/*.patch; do
        crate=$(basename "$patch_file" .patch)
        [ -d "$work/vendor/$crate" ] || {
            echo "error: $crate is not present in the vendored crates" >&2
            exit 1
        }
        cp -a "$work/vendor/$crate" "$work/patched/$crate"
        patch -d "$work/patched/$crate" -p1 < "$patch_file"
    done
fi

# Some crate archives mark their Rust sources as executable. The RPM
# build treats an executable source file with a leading "[" as a broken
# shebang when it creates the debug source package.
find "$work/vendor" -type d -exec chmod 0755 {} +
find "$work/vendor" -type f -exec chmod 0644 {} +
if [ -d "$work/patched" ]; then
    find "$work/patched" -type d -exec chmod 0755 {} +
    find "$work/patched" -type f -exec chmod 0644 {} +
fi

# The tarball holds the files as root, like the release tarballs of the
# projects do.
tar_paths=(vendor/)
[ -d "$work/patched" ] && tar_paths+=(patched/)
[ -d "$work/ui/build" ] && tar_paths+=(ui/build/)
tar --owner=0 --group=0 -cJf "$vendor_tar" -C "$work" "${tar_paths[@]}"
echo "==> wrote $(basename "$vendor_tar")"
