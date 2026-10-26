#!/bin/bash
# Build the binary RPM of a package inside a container.
#
#   .github/scripts/build-in-container.sh <package-dir> <topdir>
#
# The packages that are built from source need a toolchain that is not
# always installed on the host (the Rust ones need cargo, for example).
# The container gets the build dependencies of the spec installed, so the
# host only needs a container runtime.
#
# The sources of the package are taken from the SRPM of the topdir, the
# RPMs are written to its RPMS directory. The build itself happens in the
# container, only the RPMs are copied back to the host.

set -euo pipefail

pkg_dir=${1:?the package directory is required}
topdir=${2:?the top directory of the package is required}

# The image of the container. It needs to be a Fedora release that has
# the build dependencies of the package.
image=${BUILD_IMAGE:-fedora:44}

container=$(command -v podman 2>/dev/null || command -v docker 2>/dev/null || true)
if [ -z "$container" ]; then
    echo "error: podman or docker is needed to build the package" >&2
    echo "       (override with CONTAINER=...)" >&2
    exit 1
fi

specs=("$pkg_dir"/*.spec)
if [ ! -f "${specs[0]}" ]; then
    echo "error: no spec in $pkg_dir" >&2
    exit 1
fi
spec=${specs[0]}
name=$(grep -m1 '^Name:' "$spec" | awk '{print $2}')

srpm=$(find "$topdir/SRPMS" -name '*.src.rpm' 2>/dev/null | head -1 || true)
if [ -z "$srpm" ]; then
    echo "error: no SRPM in $topdir/SRPMS" >&2
    exit 1
fi

# The build dependencies of the spec. The pkgconfig() ones are resolved
# to the packages that provide them, dnf does not know them.
packages="rpm-build cargo cargo-rpm-macros"
requires=$(awk '/^BuildRequires:/ { print $2 }' "$spec")
for req in $requires; do
    case $req in
        pkgconfig\(*\))
            pkg=$(
                "$container" run --rm "$image" \
                    dnf repoquery --qf '%{name}' --whatprovides "$req" 2>/dev/null |
                    head -1
            )
            [ -n "$pkg" ] && packages="$packages $pkg"
            ;;
        *)
            packages="$packages $req"
            ;;
    esac
done

echo "==> building $name in the $image container"
echo "==> build dependencies: $packages"

mkdir -p "$topdir/RPMS/x86_64"

"$container" run --rm \
    -v "$topdir:/build:Z" \
    "$image" \
    bash -c "
        set -euxo pipefail
        dnf install -y $packages
        # The build happens inside the container, so the files of the
        # host keep their ownership. Only the RPMs are copied back.
        work=/tmp/build
        mkdir -p \$work/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
        rpm2archive -n /build/SRPMS/$(basename "$srpm") | tar --no-same-owner -xf - -C \$work/SOURCES
        cd \$work/SOURCES
        rpmbuild -ba --define '_topdir /tmp/build' ./*.spec
        cp \$work/RPMS/x86_64/*.rpm /build/RPMS/x86_64/
    "

echo "==> built:"
ls -1 "$topdir"/RPMS/*/*.rpm
