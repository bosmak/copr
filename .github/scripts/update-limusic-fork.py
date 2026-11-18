#!/usr/bin/env python3
"""Update the limusic-fork spec for a new upstream branch commit."""

import argparse
import datetime
import re
from pathlib import Path

SPEC = Path("limusic-fork/limusic-fork.spec")
BOT = "github-actions[bot] <github-actions[bot]@users.noreply.github.com>"


def rpm_version(upstream_version: str) -> str:
    """Convert a SemVer prerelease separator to RPM's tilde separator."""
    version = upstream_version.replace("-", "~")
    if not re.fullmatch(r"[0-9A-Za-z.+~]+", version):
        raise ValueError(f"unsupported upstream version: {upstream_version}")
    return version


def update(commit: str, upstream_version: str) -> bool:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(f"invalid commit: {commit}")

    text = SPEC.read_text()
    commit_match = re.search(r"^%global commit ([0-9a-f]{40})$", text, re.MULTILINE)
    version_match = re.search(r"^Version:\s+(\S+)$", text, re.MULTILINE)
    release_match = re.search(r"^Release:\s+(\d+)", text, re.MULTILINE)
    if not commit_match or not version_match or not release_match:
        raise ValueError(f"could not parse {SPEC}")

    if commit_match.group(1) == commit:
        return False

    version = rpm_version(upstream_version)
    if version == version_match.group(1):
        release = int(release_match.group(1)) + 1
    else:
        release = 1

    today = datetime.datetime.now(datetime.UTC).strftime("%a %b %d %Y")
    entry = (
        f"* {today} {BOT} - {version}-{release}\n"
        f"- update to upstream commit {commit}\n\n"
    )

    text = re.sub(
        r"^%global commit [0-9a-f]{40}$",
        f"%global commit {commit}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^Version:\s+\S+$",
        f"Version:        {version}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^Release:\s+\d+%\{\?dist\}$",
        f"Release:        {release}%{{?dist}}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = text.replace("%changelog\n", "%changelog\n" + entry, 1)
    SPEC.write_text(text)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    changed = update(args.commit, args.version)
    print("updated" if changed else "already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
