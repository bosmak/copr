#!/usr/bin/env python3
"""Scaffold and refresh the specs of packages that rebundle an upstream RPM.

Some upstream projects already publish an RPM for Linux. The packages in
this repository rebundle that RPM: they download it, verify it against
upstream's checksum list, unpack its payload with rpm2archive and repack
it with Fedora's directory layout.

This script does the mechanical part of that work:

    rebundle.py generate <name> <version> <rpm-url>   # new package
    rebundle.py refresh <name> <version>             # new upstream release

"generate" writes a fresh spec (and a starter README) for a package that
does not exist yet. "refresh" takes an existing spec and rewrites the parts
that come from the upstream RPM - the version, the requirements, the
installed files - while keeping the hand written parts (summary,
description, changelog) untouched.
"""

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The upstream RPMs list the libraries they need as plain sonames
# instead of as the packages that provide them. This table translates
# them into the names of the Fedora packages that ship them. The GUI
# stack of the Rust applications is dlopen()ed at runtime, so rpm's
# automatic ELF detection does not see it either.
SONAME_TO_PACKAGE = {
    "libX11.so.6": "libX11",
    "libX11-xcb.so.1": "libX11-xcb",
    "libxcb.so.1": "libxcb",
    "libXcursor.so.1": "libXcursor",
    "libXi.so.6": "libXi",
    "libxkbcommon.so.0": "libxkbcommon",
    "libxkbcommon-x11.so.0": "libxkbcommon-x11",
    "libwayland-client.so.0": "libwayland-client",
    "libvulkan.so.1": "vulkan-loader",
    "libEGL.so.1": "mesa-libEGL",
    "libasound.so.2": "alsa-lib",
    "libglvnd-egl": "mesa-libEGL",
    "libappindicator3.so.1": "libappindicator-gtk3",
    "libayatana-appindicator3.so.1": "libayatana-appindicator-gtk3",
    "libwebkit2gtk-4.1.so.0": "webkit2gtk4.1",
    "libgtk-3.so.0": "gtk3",
}

# Detected by rpm from the ELF headers, so they must not be listed by hand.
AUTO_DETECTED = (
    "libc.so.6",
    "libm.so.6",
    "libgcc_s.so.1",
    "ld-linux-",
    "rtld",
    "libdl.so.2",
    "libpthread.so.0",
)

# The names the license of a project has in its repository.
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")

SPEC_HEADER = """\
%global debug_package %{{nil}}
# Upstream ships prebuilt, already-stripped binaries. Re-running strip on
# them would mutate the ELF section metadata and diverge from upstream's
# released bytes; disabling it keeps the shipped binaries bit-identical.
%global __strip /bin/true

Name:           {name}
Version:        {version}
Release:        1%{{?dist}}
Summary:        {summary}
License:        {license}
URL:            {url}
# Upstream publishes a prebuilt RPM for Linux. We rebundle its payload:
# the very same binaries and desktop integration, repacked with Fedora's
# directory layout (licenses under /usr/share/licenses, docs under
# /usr/share/doc) so the app can be installed straight from this project.
Source0:        {source0}
"""

SPEC_REQUIRES = """\
# Upstream's own RPM requires its libraries explicitly, so we do the
# same: the sonames it lists are translated into the Fedora packages
# that provide them. Some of them are loaded with dlopen() at runtime,
# so rpm's automatic ELF dependency detection does not see them.
"""

# The comment that opens the block of requirements derived from the
# upstream RPM. Everything else in the spec is hand written and kept.
# The second one is the comment of the packages that were generated
# before it was made generic.
DERIVED_REQUIRES_MARKERS = (
    "# Upstream's own RPM requires its libraries explicitly",
    "# The GUI stack (winit/xkbcommon) is dlopen()ed",
)

SPEC_ARCH = """
# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64
"""

SPEC_PREP_CHECKSUM = """\
# Verify the downloaded RPM against upstream's checksum list.
rpm_file=%{SOURCE0}
base=$(basename "$rpm_file")
expected=$(awk -v f="$base" '$2 == f { print $1 }' @CHECKSUM@)
if [ -z "$expected" ]; then
    echo "No checksum for $base in @CHECKSUM@" >&2
    exit 1
fi
actual=$(sha256sum "$rpm_file" | awk '{ print $1 }')
if [ "$expected" != "$actual" ]; then
    echo "SHA256 mismatch for $base: expected $expected, got $actual" >&2
    exit 1
fi

"""

SPEC_PREP_NO_CHECKSUM = """\
# Upstream publishes no checksum list for its releases, so the RPM is
# fetched over TLS from the official release page. Its digest is
# recorded in the changelog.

"""

SPEC_PREP_UNPACK = """\
# Unpack the upstream RPM payload. rpm2archive turns the RPM into a tar of
# its files, so we need neither cpio nor bsdtar to read it.
mkdir -p payload
rpm2archive -n %{SOURCE0} | tar -xf - -C payload

"""

SPEC_PREP_LICENSE = """\
# The upstream RPM ships no license, so the one of the tag is used.
install -Dm644 @LICENSE@ payload/usr/share/doc/@NAME@/LICENSE

"""

SPEC_BUILD = """\
%build
# Nothing to build — we ship upstream's prebuilt binaries verbatim.
"""

SPEC_POST = """
%post
# Refresh the desktop entry, the MIME database and the icon cache. Every
# helper is optional, so a missing one is simply skipped.
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q %{_datadir}/applications || :
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database %{_datadir}/mime || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f %{_datadir}/icons/hicolor || :
fi

%postun
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q %{_datadir}/applications || :
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database %{_datadir}/mime || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f %{_datadir}/icons/hicolor || :
fi
"""


class Error(Exception):
    pass


def run(cmd, **kwargs):
    """Run a command and return its stdout."""
    try:
        out = subprocess.run(cmd, check=True, capture_output=True, **kwargs)
    except FileNotFoundError:
        raise Error(f"{cmd[0]}: command not found")
    except subprocess.CalledProcessError as exc:
        raise Error(f"{' '.join(cmd)} failed: {exc.stderr.decode().strip()}")
    return out.stdout.decode()


def rpm_query(rpm, fmt):
    return run(["rpm", "-qp", "--qf", fmt, rpm]).strip()


def unpack_payload(rpm, dest):
    """Extract the file list of an RPM into dest."""
    os.makedirs(dest, exist_ok=True)
    archive = subprocess.Popen(["rpm2archive", "-n", rpm], stdout=subprocess.PIPE)
    tar = subprocess.Popen(["tar", "-xf", "-", "-C", dest], stdin=archive.stdout)
    archive.stdout.close()
    if tar.wait() != 0:
        raise Error(f"could not unpack {rpm}")
    if archive.wait() != 0:
        raise Error(f"rpm2archive failed on {rpm}")


def payload_files(dest):
    """Every regular file of the unpacked payload, relative to dest."""
    found = []
    for root, _dirs, files in os.walk(dest):
        for f in files:
            full = os.path.join(root, f)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            found.append(os.path.relpath(full, dest))
    return sorted(found)


def normalize_dep(dep):
    """Turn one upstream requirement into a Fedora package name."""
    dep = dep.replace("(64bit)", "")
    if dep.startswith("rpmlib("):
        # The capabilities of the rpm library itself are always
        # satisfied by the rpm of the build root.
        return ""
    dep = re.sub(r"\([^)]*\)", "", dep).strip()
    if any(dep.startswith(prefix) for prefix in AUTO_DETECTED):
        return ""
    return SONAME_TO_PACKAGE.get(dep, dep)


def derive_requires(rpm):
    """The upstream requirements, translated to Fedora package names."""
    requires = []
    for line in run(["rpm", "-qpR", rpm]).splitlines():
        line = line.strip()
        if not line:
            continue
        if "(" in line and ")" in line and " or " in line:
            inner = line[line.index("(") + 1 : line.rindex(")")]
            alts = []
            for alt in inner.split():
                if alt == "or":
                    continue
                mapped = normalize_dep(alt)
                if mapped and mapped not in alts:
                    alts.append(mapped)
            if alts:
                requires.append("(" + " or ".join(alts) + ")")
            continue
        mapped = normalize_dep(line)
        if mapped and mapped not in requires:
            requires.append(mapped)
    return requires


def map_payload(name, files):
    """Map the upstream payload to Fedora's directories.

    Returns the install lines and the %files entries.
    """
    install = []
    files_lines = []
    licenses = []
    docs = []

    for f in files:
        if f.startswith("usr/bin/"):
            base = os.path.basename(f)
            install.append(
                f"install -Dm755 payload/{f} %{{buildroot}}%{{_bindir}}/{base}"
            )
            files_lines.append("%{_bindir}/" + base)
        elif f.startswith("usr/share/applications/") and f.endswith(".desktop"):
            base = os.path.basename(f)
            install.append(
                f"install -Dm644 payload/{f} %{{buildroot}}%{{_datadir}}/applications/{base}"
            )
            files_lines.append("%{_datadir}/applications/" + base)
        elif re.match(r"usr/share/(metainfo|appdata)/.*\.xml$", f):
            base = os.path.basename(f)
            subdir = os.path.basename(os.path.dirname(f))
            install.append(
                f"install -Dm644 payload/{f} %{{buildroot}}%{{_datadir}}/{subdir}/{base}"
            )
            files_lines.append(f"%{{_datadir}}/{subdir}/{base}")
        elif f.startswith("usr/share/mime/packages/"):
            base = os.path.basename(f)
            install.append(
                f"install -Dm644 payload/{f} %{{buildroot}}%{{_datadir}}/mime/packages/{base}"
            )
            files_lines.append("%{_datadir}/mime/packages/" + base)
        elif f.startswith("usr/share/man/"):
            # A man page. It is compressed by brp-compress, so the file
            # list has to match the name with the .gz suffix too.
            rel = f[len("usr/share/man/") :]
            install.append(
                f"install -Dm644 payload/{f} %{{buildroot}}%{{_mandir}}/{rel}"
            )
            files_lines.append(f"%{{_mandir}}/{rel}*")
        elif f.startswith("usr/share/bash-completion/completions/"):
            base = os.path.basename(f)
            install.append(
                f"install -Dm644 payload/{f} %{{buildroot}}%{{_datadir}}/bash-completion/completions/{base}"
            )
            files_lines.append(f"%{{_datadir}}/bash-completion/completions/{base}")
        elif f.startswith("usr/share/fish/vendor_completions.d/"):
            base = os.path.basename(f)
            install.append(
                f"install -Dm644 payload/{f} %{{buildroot}}%{{_datadir}}/fish/vendor_completions.d/{base}"
            )
            files_lines.append(f"%{{_datadir}}/fish/vendor_completions.d/{base}")
        elif f.startswith("usr/share/zsh/site-functions/"):
            base = os.path.basename(f)
            install.append(
                f"install -Dm644 payload/{f} %{{buildroot}}%{{_datadir}}/zsh/site-functions/{base}"
            )
            files_lines.append(f"%{{_datadir}}/zsh/site-functions/{base}")
        elif f.startswith("usr/share/icons/"):
            rel = f[len("usr/share/icons/") :]
            install.append(
                f"install -Dm644 payload/{f} %{{buildroot}}%{{_datadir}}/icons/{rel}"
            )
            # One glob per icon file: the same name is used in every size
            # directory, and the .attribution side files have their own.
            files_lines.append(
                f"%{{_datadir}}/icons/hicolor/*/apps/{os.path.basename(f)}"
            )
        elif f.startswith("usr/share/doc/"):
            # The upstream documents live in a directory named after the
            # app, which is not necessarily the name of this package.
            parts = f.split("/")
            rest = "/".join(parts[4:])
            base = os.path.basename(rest)
            if rest.startswith("licenses/"):
                # A license tree: keep its structure.
                install.append(
                    f"install -Dm644 payload/{f} %{{buildroot}}%{{_licensedir}}/{name}/{rest}"
                )
                licenses.append(f"%{{_licensedir}}/{name}/licenses/*")
            elif re.match(r"(LICENSE|COPYING|NOTICE|OFL-)", base):
                install.append(
                    f"install -Dm644 payload/{f} %{{buildroot}}%{{_licensedir}}/{name}/{base}"
                )
                if base.startswith("OFL-"):
                    licenses.append(f"%{{_licensedir}}/{name}/OFL-*")
                else:
                    licenses.append(f"%{{_licensedir}}/{name}/{base}")
            else:
                install.append(
                    f"install -Dm644 payload/{f} %{{buildroot}}%{{_docdir}}/{name}/{base}"
                )
                docs.append(f"%{{_docdir}}/{name}/{base}")
        elif f.startswith(f"usr/share/{name}/"):
            # Application data files (models, presets, ...).
            rel = f[len("usr/share/") :]
            install.append(
                f"install -Dm644 payload/{f} %{{buildroot}}%{{_datadir}}/{rel}"
            )
            files_lines.append(f"%{{_datadir}}/{rel}")
        else:
            print(f"warning: unhandled payload file: {f}", file=sys.stderr)

    return install, files_lines, licenses, docs


def unique(seq):
    seen = set()
    out = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def payload_has_license(payload_dir):
    """Whether the payload of the upstream RPM holds a license."""
    return any(
        os.path.basename(f).startswith(("LICENSE", "COPYING", "NOTICE"))
        for f in payload_files(payload_dir)
    )


def upstream_repo(source0):
    """The GitHub repository and the tag prefix of an upstream URL."""
    m = re.match(
        r"^https?://github\.com/([^/]+/[^/]+)/releases/download/([^/%]+)%\{version\}",
        source0,
    )
    if not m:
        return "", ""
    return m.group(1), m.group(2)


def url_exists(url):
    """Whether a URL answers."""
    return (
        subprocess.run(
            ["curl", "-fsSLI", url],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def guess_license_url(source0, version):
    """The license of the upstream tag, when the RPM ships none.

    Upstream does not always put its license in the RPM, so the one of
    the tag is used instead.
    """
    repo, prefix = upstream_repo(source0)
    if not repo:
        return ""
    for name in LICENSE_NAMES:
        url = f"https://raw.githubusercontent.com/{repo}/{prefix}{version}/{name}"
        if url_exists(url):
            return url.replace(version, "%{version}")
    return ""


def fetch_license(url, version, dest):
    """Download the license of the upstream tag."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    run(["curl", "-fsSL", url.replace("%{version}", version), "-o", dest])


def source_macro(sources, role):
    """The macro of the source with a role, if the package has one."""
    for index, source in enumerate(sources):
        if source["role"] == role:
            return f"%{{SOURCE{index}}}"
    return ""


def render_prep(name, sources):
    """The prep and build sections of the spec.

    The checksum list and the license are both optional: upstream does
    not always publish a checksum list, and its RPM does not always
    ship the license.
    """
    checksum = source_macro(sources, "checksum")
    license_ = source_macro(sources, "license")
    out = ["\n%prep\n"]
    if checksum:
        out.append(SPEC_PREP_CHECKSUM.replace("@CHECKSUM@", checksum))
    else:
        out.append(SPEC_PREP_NO_CHECKSUM)
    out.append(SPEC_PREP_UNPACK)
    if license_:
        out.append(
            SPEC_PREP_LICENSE.replace("@LICENSE@", license_).replace("@NAME@", name)
        )
    out.append(SPEC_BUILD)
    return "".join(out)


def render_spec(
    name,
    version,
    summary,
    license_,
    url,
    sources,
    requires,
    extras,
    description,
    install,
    files_lines,
    licenses,
    docs,
    changelog,
):
    out = [
        SPEC_HEADER.format(
            name=name,
            version=version,
            summary=summary,
            license=license_,
            url=url,
            source0=sources[0]["url"],
        )
    ]
    for index, source in enumerate(sources[1:], start=1):
        out.append(source["comment"] + "\n")
        out.append(f"Source{index}:        {source['url']}\n")
    if requires:
        out.append("\n")
        out.append(SPEC_REQUIRES)
        out.extend(f"Requires:       {r}\n" for r in requires)
    for extra in extras:
        out.append(extra + "\n")
    out.append(SPEC_ARCH)
    out.append(f"\n%description\n{description.rstrip()}\n")
    out.append(render_prep(name, sources))
    out.append("\n%install\n")
    out.extend(line + "\n" for line in install)
    out.append(SPEC_POST)
    out.append("\n%files\n")
    out.extend(f"%license {l}\n" for l in unique(licenses))
    out.extend(f"%doc {d}\n" for d in unique(docs))
    out.extend(line + "\n" for line in unique(files_lines))
    out.append("\n%changelog\n")
    out.append(changelog.strip("\n") + "\n")
    return "".join(out)


def update_spec(text, version, requires, install, files_lines, licenses, docs, entry):
    """Update the parts of a spec that come from the upstream RPM.

    Everything else - the summary, the description, the hand written
    requirements, the comments - is left untouched, so the diff of an
    update stays small.
    """
    # The version and the release.
    text = re.sub(
        r"^Version:.*$", f"Version:        {version}", text, count=1, flags=re.MULTILINE
    )
    text = re.sub(
        r"^Release:.*$", "Release:        1%{?dist}", text, count=1, flags=re.MULTILINE
    )

    # The requirements derived from the upstream RPM.
    derived = re.compile(
        r"^(?:"
        + "|".join(re.escape(marker) for marker in DERIVED_REQUIRES_MARKERS)
        + r")[^\n]*\n(?:#[^\n]*\n)*(?:Requires:[ \t][^\n]*\n)*",
        re.MULTILINE,
    )
    if requires:
        block = SPEC_REQUIRES + "".join(f"Requires:       {r}\n" for r in requires)
    else:
        block = ""
    text = derived.sub(lambda _m: block, text, count=1)

    # The installed files.
    body = "".join(line + "\n" for line in install) + "\n"
    text = re.sub(
        r"(?<=^%install\n).*?(?=^%post)",
        body,
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )

    # The file list.
    body = "".join(f"%license {l}\n" for l in unique(licenses))
    body += "".join(f"%doc {d}\n" for d in unique(docs))
    body += "".join(line + "\n" for line in unique(files_lines)) + "\n"
    text = re.sub(
        r"(?<=^%files\n).*?(?=^%changelog)",
        body,
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )

    # The changelog.
    if entry:
        text = re.sub(
            r"^(%changelog\n)",
            r"\1" + entry + "\n\n",
            text,
            count=1,
            flags=re.MULTILINE,
        )

    return text


def spec_sources(text):
    """The sources of a spec, indexed by their number."""
    sources = {}
    for number, url in re.findall(
        r"^Source(\d+):[ \t]*(\S+)[ \t]*$", text, re.MULTILINE
    ):
        sources[int(number)] = url
    return sources


def find_license_source(sources):
    """The number and the URL of the source that holds the license.

    Only a source that is fetched over the network is of interest here:
    the license of a package that is vendored in this repository is not
    downloaded again.
    """
    for number, url in sorted(sources.items()):
        base = url.rsplit("/", 1)[-1].split("#")[-1]
        if base in LICENSE_NAMES and url.startswith("http"):
            return number, url
    return None, ""


def guess_sha_url(source0, version):
    """The checksum file that sits next to the upstream RPM."""
    base = source0.replace("%{version}", version).rsplit("/", 1)[0]
    for candidate in ("SHA256SUMS.txt", "SHA256SUMS", "sha256sums.txt"):
        url = f"{base}/{candidate}"
        if url_exists(url):
            # Keep the version placeholder, so the spec can be bumped
            # without touching it.
            return url.replace(version, "%{version}")
    return ""


def fetch_rpm(url, version, rpm_file):
    tmpdir = tempfile.mkdtemp(prefix="rebundle-")
    path = os.path.join(tmpdir, "upstream.rpm")
    if rpm_file:
        shutil.copyfile(rpm_file, path)
    else:
        resolved = url.replace("%{version}", version)
        run(["curl", "-fsSL", resolved, "-o", path])
    return tmpdir, path


def cmd_generate(args):
    pkg_dir = os.path.join(REPO_ROOT, args.name)
    if os.path.exists(pkg_dir):
        raise Error(f"{pkg_dir} already exists")

    tmpdir, rpm = fetch_rpm(args.rpm_url, args.version, args.rpm_file)
    try:
        payload_dir = os.path.join(tmpdir, "payload")
        unpack_payload(rpm, payload_dir)

        summary = args.summary or rpm_query(rpm, "%{SUMMARY}").replace("\n", " ")
        license_ = args.license or rpm_query(rpm, "%{LICENSE}")
        url = args.url or rpm_query(rpm, "%{URL}")
        requires = derive_requires(rpm)

        # The sources of the package: the RPM of upstream, its checksum
        # list when it publishes one, and the license of the tag when
        # the RPM ships none.
        sources = [
            {
                "comment": "",
                "url": args.rpm_url,
                "role": "rpm",
            }
        ]
        checksum_url = "" if args.no_sha else guess_sha_url(args.rpm_url, args.version)
        if checksum_url:
            sources.append(
                {
                    "comment": (
                        "# Upstream's checksum list, used in the prep section to"
                        " verify Source0."
                    ),
                    "url": checksum_url,
                    "role": "checksum",
                }
            )
        license_url = ""
        if not payload_has_license(payload_dir):
            license_url = guess_license_url(args.rpm_url, args.version)
        if license_url:
            sources.append(
                {
                    "comment": (
                        "# The upstream RPM ships no license, so the one of the"
                        " tag is used."
                    ),
                    "url": license_url,
                    "role": "license",
                }
            )
            fetch_license(
                license_url,
                args.version,
                os.path.join(payload_dir, "usr", "share", "doc", args.name, "LICENSE"),
            )

        install, files_lines, licenses, docs = map_payload(
            args.name, payload_files(payload_dir)
        )

        description = (
            args.description or "TODO: describe the package in a few sentences."
        )
        changelog = (
            f"* {datetime.datetime.now().strftime('%a %b %d %Y')}"
            f" Gustavo Bosmak <gustavo.bosmak@gmail.com> - {args.version}-1\n"
            "- initial COPR package (rebundle of the upstream RPM)"
        )

        spec = render_spec(
            args.name,
            args.version,
            summary,
            license_,
            url,
            sources,
            requires,
            [],
            description,
            install,
            files_lines,
            licenses,
            docs,
            changelog,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    os.makedirs(pkg_dir)
    with open(os.path.join(pkg_dir, f"{args.name}.spec"), "w") as f:
        f.write(spec)

    with open(os.path.join(pkg_dir, "README.md"), "w") as f:
        f.write(
            f"# {args.name}\n\n{summary}\n\n"
            "## This package is a rebundle\n\n"
            "Upstream publishes an RPM for Linux; this package repacks its payload\n"
            "with Fedora's directory layout. The binaries are byte-identical to\n"
            "upstream's.\n\n"
            "## Install\n\n"
            "```sh\nsudo dnf copr enable bosmak/copr\n"
            f"sudo dnf install {args.name}\n```\n\n"
            f"Upstream: {url}\n"
        )

    print(f"created {args.name}/{args.name}.spec")
    print(f"Next: fill in the %description, then run 'make {args.name}-rpm'")


def cmd_refresh(args):
    spec_path = os.path.join(REPO_ROOT, args.name, f"{args.name}.spec")
    if not os.path.exists(spec_path):
        raise Error(f"{spec_path} does not exist")

    with open(spec_path) as f:
        text = f.read()

    sources = spec_sources(text)
    source0 = sources.get(0, "")
    if not source0:
        raise Error(f"{spec_path} has no Source0")

    tmpdir, rpm = fetch_rpm(source0, args.version, args.rpm_file)
    try:
        payload_dir = os.path.join(tmpdir, "payload")
        unpack_payload(rpm, payload_dir)

        # The RPM of upstream does not ship a license, so the one of the
        # tag is used. It has to be in the payload before it is mapped,
        # or the license would be missing from the package.
        _, license_url = find_license_source(sources)
        if license_url and not payload_has_license(payload_dir):
            fetch_license(
                license_url,
                args.version,
                os.path.join(payload_dir, "usr", "share", "doc", args.name, "LICENSE"),
            )

        requires = derive_requires(rpm)
        install, files_lines, licenses, docs = map_payload(
            args.name, payload_files(payload_dir)
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if args.no_changelog:
        entry = ""
    else:
        today = datetime.datetime.now().strftime("%a %b %d %Y")
        bot = args.author
        entry = f"* {today} {bot} - {args.version}-1\n- update to {args.version}"

    spec = update_spec(
        text, args.version, requires, install, files_lines, licenses, docs, entry
    )

    with open(spec_path, "w") as f:
        f.write(spec)

    print(f"refreshed {args.name} to {args.version}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="write a new spec for a rebundled package")
    gen.add_argument("name")
    gen.add_argument("version")
    gen.add_argument("rpm_url")
    gen.add_argument("--summary")
    gen.add_argument("--license")
    gen.add_argument("--url")
    gen.add_argument("--description")
    gen.add_argument("--rpm-file", help="inspect a local RPM instead of downloading it")
    gen.add_argument("--no-sha", action="store_true")
    gen.set_defaults(func=cmd_generate)

    ref = sub.add_parser(
        "refresh", help="update an existing spec from a new upstream release"
    )
    ref.add_argument("name")
    ref.add_argument("version")
    ref.add_argument("--rpm-file", help="inspect a local RPM instead of downloading it")
    ref.add_argument(
        "--author",
        default="github-actions[bot] <github-actions[bot]@users.noreply.github.com>",
        help="who to credit in the changelog entry",
    )
    ref.add_argument(
        "--no-changelog",
        action="store_true",
        help="do not add a changelog entry (used to re-render a spec in place)",
    )
    ref.set_defaults(func=cmd_refresh)

    args = parser.parse_args()
    try:
        args.func(args)
    except Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
