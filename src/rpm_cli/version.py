"""Fuzzy version resolution using git ls-remote and PEP 440 specifiers.

Resolves version specifiers like ``~=1.0.0``, ``>=1.0.0,<2.0.0``, ``*``
against available git tags using the ``packaging`` library.
"""

import re
import subprocess
import sys

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

_PEP440_OPERATOR_RE = re.compile(r"[~=><!*]")


def resolve_version(url: str, rev_spec: str) -> str:
    """Resolve a version specifier against git tags.

    Args:
        url: Git repository URL.
        rev_spec: Version specifier (branch/tag name or PEP 440 specifier).

    Returns:
        The resolved tag or branch name.

    Raises:
        SystemExit: If no matching version is found.
    """
    if not _PEP440_OPERATOR_RE.search(rev_spec):
        return rev_spec

    tags = _list_tags(url)
    if not tags:
        print(
            f"Error: No tags found for {url}",
            file=sys.stderr,
        )
        sys.exit(1)

    versions = _parse_tag_versions(tags)
    if not versions:
        print(
            f"Error: No parseable version tags found for {url}",
            file=sys.stderr,
        )
        sys.exit(1)

    if rev_spec == "*":
        best = max(versions, key=lambda pair: pair[1])
        return best[0]

    specifier = SpecifierSet(rev_spec)
    matching = [(tag, ver) for tag, ver in versions if ver in specifier]

    if not matching:
        print(
            f"Error: No tag matching '{rev_spec}' found for {url}. Available versions: {[str(v) for _, v in versions]}",
            file=sys.stderr,
        )
        sys.exit(1)

    best = max(matching, key=lambda pair: pair[1])
    return best[0]


def _list_tags(url: str) -> list[str]:
    """Run ``git ls-remote --tags`` and return tag ref names.

    Args:
        url: Git repository URL.

    Returns:
        List of tag names (without ``refs/tags/`` prefix).

    Raises:
        SystemExit: If git ls-remote fails.
    """
    result = subprocess.run(
        ["git", "ls-remote", "--tags", url],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            f"Error: git ls-remote failed for {url}: {result.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)

    tags = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        ref = parts[1]
        if ref.startswith("refs/tags/") and not ref.endswith("^{}"):
            tag_name = ref.removeprefix("refs/tags/")
            tags.append(tag_name)
    return tags


def _parse_tag_versions(tags: list[str]) -> list[tuple[str, Version]]:
    """Parse version from tag names.

    Tries to parse each tag as a PEP 440 version. Tags that
    don't parse as valid versions are skipped.

    Args:
        tags: List of tag names.

    Returns:
        List of (tag_name, Version) tuples.
    """
    versions = []
    for tag in tags:
        try:
            ver = Version(tag)
            versions.append((tag, ver))
        except InvalidVersion:
            # Try extracting version from the last path segment
            if "/" in tag:
                last_segment = tag.rsplit("/", 1)[-1]
                try:
                    ver = Version(last_segment)
                    versions.append((tag, ver))
                except InvalidVersion:
                    continue
    return versions
