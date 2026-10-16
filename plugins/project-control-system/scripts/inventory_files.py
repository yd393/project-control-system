#!/usr/bin/env python3
"""Read-only file inventory and duplicate-content detection.

Scans a directory tree and reports facts that help plan a file organization
task: file counts, logical sizes, extensions, modification time range, large
files, nested project boundaries, skipped paths and scan errors. With
``--duplicates`` it also groups files with identical content (SHA-256).

The scanner never writes files, never follows internal symlinks, never reads
file contents for classification and never runs anything found in the tree.
Duplicate groups are candidates with identical content, not permission to
delete anything.

Exit codes: 0 complete scan, 1 partial scan, 2 invalid root or arguments.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path, PurePosixPath


SCHEMA_VERSION = 1
CHUNK_SIZE = 1024 * 1024
TOP_FILES = 10

DEFAULT_PRUNED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".file-organization",
    }
)
IGNORED_FILES = frozenset({".DS_Store"})
PROJECT_MARKERS = (".git", "AGENTS.md", "project-control", ".ai", ".opencode")


class InvalidRootError(ValueError):
    """The requested root does not exist or is not a directory."""


class FileChangedError(OSError):
    """A file changed while it was being hashed or after it was listed."""


def scan_inventory(
    root: Path,
    *,
    duplicates: bool = False,
    excludes: tuple[str, ...] = (),
) -> dict[str, object]:
    """Scan ``root`` and return a schema_version=1 report.

    Raises ``InvalidRootError`` when ``root`` is missing or not a directory.
    """
    root_path = Path(root).expanduser()
    try:
        resolved = root_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise InvalidRootError(f"root does not exist: {root_path}") from exc
    if not resolved.is_dir():
        raise InvalidRootError(f"root is not a directory: {resolved}")

    files: list[dict[str, object]] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    _walk(resolved, "", tuple(excludes), files, skipped, errors)

    files.sort(key=lambda item: item["path"])
    skipped.sort(key=lambda item: item["path"])

    duplicate_groups: list[dict[str, object]] = []
    reclaimable: int | None = None
    if duplicates:
        duplicate_groups, reclaimable = _find_duplicates(resolved, files, errors)
    errors.sort(key=lambda item: item["path"])

    report = _empty_report(str(resolved))
    report.update(
        complete=not errors,
        summary=_summarize(files, reclaimable),
        files=files,
        duplicate_groups=duplicate_groups,
        hardlink_groups=_hardlink_groups(files),
        skipped=skipped,
        errors=errors,
    )
    return report


def _walk(
    directory: Path,
    rel_dir: str,
    excludes: tuple[str, ...],
    files: list[dict[str, object]],
    skipped: list[dict[str, str]],
    errors: list[dict[str, str]],
) -> None:
    try:
        with os.scandir(os.fspath(directory)) as iterator:
            entries = sorted(iterator, key=lambda entry: entry.name)
    except OSError as exc:
        errors.append(_error(rel_dir or ".", exc))
        return

    for entry in entries:
        rel = f"{rel_dir}/{entry.name}" if rel_dir else entry.name
        try:
            if entry.is_symlink():
                skipped.append({"path": rel, "reason": "symlink"})
                continue
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError as exc:
            errors.append(_error(rel, exc))
            continue

        if is_dir:
            if entry.name in DEFAULT_PRUNED_DIRS:
                skipped.append({"path": rel, "reason": "default_excluded"})
            elif _is_excluded(rel, excludes):
                skipped.append({"path": rel, "reason": "excluded"})
            elif _is_project(Path(entry.path)):
                skipped.append({"path": rel, "reason": "nested_project"})
            else:
                _walk(Path(entry.path), rel, excludes, files, skipped, errors)
            continue

        if entry.name in IGNORED_FILES:
            continue
        if _is_excluded(rel, excludes):
            skipped.append({"path": rel, "reason": "excluded"})
            continue
        try:
            info = os.lstat(entry.path)
        except OSError as exc:
            errors.append(_error(rel, exc))
            continue
        if not stat.S_ISREG(info.st_mode):
            skipped.append({"path": rel, "reason": "not_regular_file"})
            continue
        files.append(
            {
                "path": rel,
                "size": info.st_size,
                "mtime_ns": info.st_mtime_ns,
                "device": info.st_dev,
                "inode": info.st_ino,
            }
        )


def _is_excluded(rel: str, excludes: tuple[str, ...]) -> bool:
    path = PurePosixPath(rel)
    return any(path.match(pattern) for pattern in excludes)


def _is_project(directory: Path) -> bool:
    return any(os.path.lexists(directory / marker) for marker in PROJECT_MARKERS)


def _hash_stable_file(path: Path) -> str:
    """Return the SHA-256 of ``path``; raise FileChangedError if it changes."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        before = os.fstat(handle.fileno())
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    after = os.lstat(path)
    if _identity(before) != _identity(after):
        raise FileChangedError(f"file changed while hashing: {path}")
    return digest.hexdigest()


def _identity(info: os.stat_result) -> tuple[int, int, int, int]:
    return (info.st_size, info.st_mtime_ns, info.st_dev, info.st_ino)


def _find_duplicates(
    root: Path,
    files: list[dict[str, object]],
    errors: list[dict[str, str]],
) -> tuple[list[dict[str, object]], int]:
    # size -> (device, inode) -> paths
    by_size: dict[int, dict[tuple[int, int], list[dict[str, object]]]] = {}
    for item in files:
        key = (item["device"], item["inode"])
        by_size.setdefault(item["size"], {}).setdefault(key, []).append(item)

    groups: list[dict[str, object]] = []
    reclaimable = 0
    for size in sorted(by_size):
        inodes = by_size[size]
        if len(inodes) < 2:
            continue
        by_hash: dict[str, list[list[dict[str, object]]]] = {}
        for members in inodes.values():
            digest = _hash_inode(root, members, errors)
            if digest is not None:
                by_hash.setdefault(digest, []).append(members)
        for digest, inode_members in by_hash.items():
            if len(inode_members) < 2:
                continue
            paths = sorted(item["path"] for members in inode_members for item in members)
            groups.append({"size": size, "sha256": digest, "paths": paths})
            reclaimable += (len(inode_members) - 1) * size

    groups.sort(key=lambda group: (-group["size"], group["paths"][0]))
    return groups, reclaimable


def _hash_inode(
    root: Path,
    members: list[dict[str, object]],
    errors: list[dict[str, str]],
) -> str | None:
    """Hash one path of an inode; any failure drops the whole inode."""
    item = members[0]
    path = root / item["path"]
    expected = (item["size"], item["mtime_ns"], item["device"], item["inode"])
    try:
        digest = _hash_stable_file(path)
        if _identity(os.lstat(path)) != expected:
            raise FileChangedError(f"file changed after it was listed: {path}")
    except OSError as exc:
        errors.append(_error(item["path"], exc))
        return None
    return digest


def _hardlink_groups(files: list[dict[str, object]]) -> list[dict[str, object]]:
    by_inode: dict[tuple[int, int], list[dict[str, object]]] = {}
    for item in files:
        by_inode.setdefault((item["device"], item["inode"]), []).append(item)
    groups = [
        {
            "device": device,
            "inode": inode,
            "size": members[0]["size"],
            "paths": sorted(item["path"] for item in members),
        }
        for (device, inode), members in by_inode.items()
        if len(members) > 1
    ]
    groups.sort(key=lambda group: group["paths"][0])
    return groups


def _summarize(
    files: list[dict[str, object]], reclaimable: int | None
) -> dict[str, object]:
    extensions: dict[str, dict[str, int]] = {}
    for item in files:
        suffix = PurePosixPath(item["path"]).suffix.lower()
        bucket = extensions.setdefault(suffix, {"count": 0, "bytes": 0})
        bucket["count"] += 1
        bucket["bytes"] += item["size"]
    mtimes = [item["mtime_ns"] for item in files]
    return {
        "file_count": len(files),
        "logical_bytes": sum(item["size"] for item in files),
        "extensions": dict(sorted(extensions.items())),
        "oldest_mtime_ns": min(mtimes) if mtimes else None,
        "newest_mtime_ns": max(mtimes) if mtimes else None,
        "estimated_reclaimable_bytes": reclaimable,
    }


def _empty_report(root: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "root": root,
        "complete": False,
        "summary": _summarize([], None),
        "files": [],
        "duplicate_groups": [],
        "hardlink_groups": [],
        "skipped": [],
        "errors": [],
    }


def _error(rel: str, exc: BaseException) -> dict[str, str]:
    if isinstance(exc, FileChangedError):
        kind = "changed_during_scan"
    elif isinstance(exc, PermissionError):
        kind = "permission_denied"
    elif isinstance(exc, FileNotFoundError):
        kind = "not_found"
    else:
        kind = "os_error"
    return {"path": rel, "kind": kind, "message": str(exc)}


def render_text(report: dict[str, object]) -> str:
    summary = report["summary"]
    lines = [
        f"Root: {report['root']}",
        f"Complete: {'yes' if report['complete'] else 'no'}",
        f"Files: {summary['file_count']}",
        f"Logical bytes: {summary['logical_bytes']}",
    ]
    if summary["extensions"]:
        lines.append("Extensions:")
        for suffix, bucket in summary["extensions"].items():
            label = suffix or "(none)"
            lines.append(f"  {label}: {bucket['count']} files, {bucket['bytes']} bytes")

    largest = sorted(report["files"], key=lambda item: (-item["size"], item["path"]))
    if largest:
        lines.append(f"Largest files (top {min(TOP_FILES, len(largest))}):")
        for item in largest[:TOP_FILES]:
            lines.append(f"  {item['size']:>12}  {item['path']}")

    if summary["estimated_reclaimable_bytes"] is not None:
        lines.append(
            f"Duplicate groups: {len(report['duplicate_groups'])} "
            f"(estimated reclaimable logical bytes: "
            f"{summary['estimated_reclaimable_bytes']}; candidates only)"
        )
        for group in report["duplicate_groups"]:
            lines.append(f"  {group['size']} bytes x {len(group['paths'])}:")
            lines.extend(f"    {path}" for path in group["paths"])
    if report["hardlink_groups"]:
        lines.append(f"Hardlink groups: {len(report['hardlink_groups'])}")
        for group in report["hardlink_groups"]:
            lines.append(f"  {', '.join(group['paths'])}")
    if report["skipped"]:
        lines.append(f"Skipped: {len(report['skipped'])}")
        for item in report["skipped"]:
            lines.append(f"  {item['path']} ({item['reason']})")
    if report["errors"]:
        lines.append(f"Errors: {len(report['errors'])}")
        for item in report["errors"]:
            lines.append(f"  {item['path']} [{item['kind']}] {item['message']}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inventory of a directory: counts, sizes, extensions, "
            "nested project boundaries and optional duplicate-content groups."
        )
    )
    parser.add_argument("root", help="Directory to scan.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the JSON report on stdout instead of text.",
    )
    parser.add_argument(
        "--duplicates",
        action="store_true",
        help="Hash same-size candidates (SHA-256) and report duplicate content.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help=(
            "Root-relative POSIX glob, matched with PurePosixPath.match; "
            "matching directories are pruned. Repeatable. Not gitignore syntax."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = scan_inventory(
            Path(args.root),
            duplicates=args.duplicates,
            excludes=tuple(args.exclude),
        )
        code = 0 if report["complete"] else 1
    except InvalidRootError as exc:
        report = _empty_report(os.path.abspath(os.path.expanduser(args.root)))
        report["errors"] = [{"path": ".", "kind": "invalid_root", "message": str(exc)}]
        print(f"inventory_files: {exc}", file=sys.stderr)
        code = 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_text(report))
    return code


if __name__ == "__main__":
    sys.exit(main())
