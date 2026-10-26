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

# The upstream RPMs are built outside of Fedora: some of them depend on
# plain sonames instead of on the packages that provide them. rpm's
# automatic ELF detection does not see them either, the GUI stack is
# dlopen()ed at runtime.
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

SPEC_SOURCE1 = """\
# Upstream's checksum list, used in the prep section to verify Source0.
Source1:        {source1}
"""

SPEC_REQUIRES = """\
# The GUI stack (winit/xkbcommon) is dlopen()ed at runtime, so rpm's
# automatic ELF dependency detection does not see it. Upstream's own RPM
# requires these explicitly, so we do the same.
"""

# The comment that opens the block of requirements derived from the
# upstream RPM. Everything else in the spec is hand written and kept.
DERIVED_REQUIRES_MARKER = "# The GUI stack (winit/xkbcommon) is dlopen()ed"

SPEC_ARCH = """
# Upstream only publishes x86_64 Linux builds.
ExclusiveArch:  x86_64
"""

SPEC_PREP = """
%prep
# Verify the downloaded RPM against upstream's checksum list.
rpm_file=%{SOURCE0}
base=$(basename "$rpm_file")
expected=$(awk -v f="$base" '$2 == f { print $1 }' %{SOURCE1})
if [ -z "$expected" ]; then
    echo "No checksum for $base in %{SOURCE1}" >&2
    exit 1
fi
actual=$(sha256sum "$rpm_file" | awk '{ print $1 }')
if [ "$expected" != "$actual" ]; then
    echo "SHA256 mismatch for $base: expected $expected, got $actual" >&2
    exit 1
fi

# Unpack the upstream RPM payload. rpm2archive turns the RPM into a tar of
# its files, so we need neither cpio nor bsdtar to read it.
mkdir -p payload
rpm2archive -n %{SOURCE0} | tar -xf - -C payload

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


def render_spec(
    name,
    version,
    summary,
    license_,
    url,
    source0,
    source1,
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
            source0=source0,
        )
    ]
    if source1:
        out.append(SPEC_SOURCE1.format(source1=source1))
    if requires:
        out.append("\n")
        out.append(SPEC_REQUIRES)
        out.extend(f"Requires:       {r}\n" for r in requires)
    for extra in extras:
        out.append(extra + "\n")
    out.append(SPEC_ARCH)
    out.append(f"\n%description\n{description.rstrip()}\n")
    out.append(SPEC_PREP)
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


def split_requirements(text):
    """The block of requirements derived from the upstream RPM.

    It is the marker comment plus the plain "Requires:" lines that follow
    it. Everything else (a "Requires(post):", a "Recommends:", ...) was
    added by hand and is left alone.
    """
    lines = text.splitlines()
    derived = []
    in_derived = False

    for line in lines:
        if line.startswith(DERIVED_REQUIRES_MARKER):
            in_derived = True
            derived.append(line)
            continue
        if in_derived:
            if line.startswith("#") or re.match(r"^Requires:[ \t]", line):
                derived.append(line)
                continue
            in_derived = False

    return derived


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
        r"^"
        + re.escape(DERIVED_REQUIRES_MARKER)
        + r"[^\n]*\n(?:#[^\n]*\n)*(?:Requires:[ \t][^\n]*\n)*",
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


def spec_fields(text):
    """Pull the hand written parts out of an existing spec."""
    fields = {}

    def grab(pattern, key):
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            fields[key] = m.group(1).strip()

    grab(r"^Summary:[ \t]*(.*)$", "summary")
    grab(r"^License:[ \t]*(.*)$", "license")
    grab(r"^URL:[ \t]*(.*)$", "url")
    grab(r"^Source0:[ \t]*(.*)$", "source0")
    grab(r"^Source1:[ \t]*(.*)$", "source1")

    m = re.search(r"^%description\n(.*?)(?=^%\w)", text, re.MULTILINE | re.DOTALL)
    if m:
        fields["description"] = m.group(1).strip("\n")

    m = re.search(r"^%changelog\n(.*)", text, re.MULTILINE | re.DOTALL)
    if m:
        fields["changelog"] = m.group(1).strip("\n")

    return fields


def guess_sha_url(source0, version):
    """The checksum file that sits next to the upstream RPM."""
    base = source0.replace("%{version}", version).rsplit("/", 1)[0]
    for candidate in ("SHA256SUMS.txt", "SHA256SUMS", "sha256sums.txt"):
        url = f"{base}/{candidate}"
        if (
            subprocess.run(
                ["curl", "-fsSLI", url],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        ):
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
        install, files_lines, licenses, docs = map_payload(
            args.name, payload_files(payload_dir)
        )
        source1 = "" if args.no_sha else guess_sha_url(args.rpm_url, args.version)

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
            args.rpm_url,
            source1,
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
    fields = spec_fields(text)

    source0 = fields.get("source0", "")
    if not source0:
        raise Error(f"{spec_path} has no Source0")

    tmpdir, rpm = fetch_rpm(source0, args.version, args.rpm_file)
    try:
        payload_dir = os.path.join(tmpdir, "payload")
        unpack_payload(rpm, payload_dir)
        requires = derive_requires(rpm)
        install, files_lines, licenses, docs = map_payload(
            args.name, payload_files(payload_dir)
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    source1 = fields.get("source1", "")
    if not source1:
        source1 = guess_sha_url(source0, args.version)

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
