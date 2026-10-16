"""Tests for scripts/inventory_files.py.

All fixtures live in temporary directories; no real user directory is scanned.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "inventory_files.py"


def load_module():
    spec = importlib.util.spec_from_file_location("inventory_files", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["inventory_files"] = module
    spec.loader.exec_module(module)
    return module


inventory = load_module()


def write(path: Path, content: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def paths_of(report: dict) -> list[str]:
    return [item["path"] for item in report["files"]]


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    result = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[rel] = (os.readlink(path).encode(), 0)
            elif path.is_file():
                result[rel] = (path.read_bytes(), path.stat().st_mtime_ns)
            else:
                result[rel] = (b"<dir>", 0)
    return result


class TempDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()


class InventoryTests(TempDirTestCase):
    def test_inventory_summary(self) -> None:
        write(self.root / "a.txt", "abc")
        write(self.root / "sub" / "b.TXT", "def")

        report = inventory.scan_inventory(self.root)

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["root"], str(self.root))
        self.assertTrue(report["complete"])
        summary = report["summary"]
        self.assertEqual(summary["file_count"], 2)
        self.assertEqual(summary["logical_bytes"], 6)
        self.assertEqual(summary["extensions"][".txt"], {"count": 2, "bytes": 6})
        self.assertEqual(paths_of(report), ["a.txt", "sub/b.TXT"])
        for item in report["files"]:
            self.assertEqual(set(item), {"path", "size", "mtime_ns", "device", "inode"})
        self.assertIsNotNone(summary["oldest_mtime_ns"])
        self.assertLessEqual(summary["oldest_mtime_ns"], summary["newest_mtime_ns"])

    def test_top_level_schema(self) -> None:
        report = inventory.scan_inventory(self.root)
        self.assertEqual(
            set(report),
            {
                "schema_version",
                "root",
                "complete",
                "summary",
                "files",
                "duplicate_groups",
                "hardlink_groups",
                "skipped",
                "errors",
            },
        )

    def test_no_extension(self) -> None:
        write(self.root / "Makefile", "x")
        report = inventory.scan_inventory(self.root)
        self.assertEqual(report["summary"]["extensions"], {"": {"count": 1, "bytes": 1}})

    def test_empty_directory(self) -> None:
        report = inventory.scan_inventory(self.root)
        self.assertTrue(report["complete"])
        self.assertEqual(report["summary"]["file_count"], 0)
        self.assertEqual(report["summary"]["logical_bytes"], 0)
        self.assertIsNone(report["summary"]["oldest_mtime_ns"])
        self.assertIsNone(report["summary"]["newest_mtime_ns"])
        self.assertEqual(report["files"], [])

    def test_nested_project_boundary(self) -> None:
        write(self.root / "loose.pdf", "pdf")
        write(self.root / "repo" / ".git", "gitdir: elsewhere")
        write(self.root / "repo" / "src" / "main.py", "print()")
        write(self.root / "managed" / "AGENTS.md", "# agents")
        write(self.root / "managed" / "notes.md", "notes")
        for marker in ("project-control", ".ai", ".opencode"):
            (self.root / f"p-{marker.strip('.')}" / marker).mkdir(parents=True)
            write(self.root / f"p-{marker.strip('.')}" / "inner.txt", "x")

        report = inventory.scan_inventory(self.root)

        self.assertEqual(paths_of(report), ["loose.pdf"])
        boundaries = {
            item["path"] for item in report["skipped"] if item["reason"] == "nested_project"
        }
        self.assertEqual(
            boundaries,
            {"repo", "managed", "p-project-control", "p-ai", "p-opencode"},
        )
        self.assertTrue(report["complete"])

    def test_root_project_still_scanned(self) -> None:
        write(self.root / "AGENTS.md", "# agents")
        (self.root / ".git").mkdir()
        write(self.root / ".git" / "HEAD", "ref")
        write(self.root / "project-control" / "status.md", "status")
        write(self.root / "docs" / "a.md", "a")

        report = inventory.scan_inventory(self.root)

        self.assertEqual(
            paths_of(report), ["AGENTS.md", "docs/a.md", "project-control/status.md"]
        )
        self.assertIn({"path": ".git", "reason": "default_excluded"}, report["skipped"])

    def test_symlinks_and_hidden_files(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            write(Path(outside) / "secret.txt", "outside")
            write(self.root / ".hidden.txt", "h")
            write(self.root / ".config" / "settings.json", "{}")
            write(self.root / ".DS_Store", "junk")
            write(self.root / "node_modules" / "pkg" / "index.js", "x")
            write(self.root / "deep" / "__pycache__" / "m.pyc", "x")
            write(self.root / ".file-organization" / "run.md", "log")
            os.symlink(outside, self.root / "out-link")
            os.symlink(self.root, self.root / "loop")
            os.symlink(self.root / ".hidden.txt", self.root / "file-link")

            report = inventory.scan_inventory(self.root)

        self.assertEqual(paths_of(report), [".config/settings.json", ".hidden.txt"])
        skipped = {item["path"]: item["reason"] for item in report["skipped"]}
        self.assertEqual(skipped["out-link"], "symlink")
        self.assertEqual(skipped["loop"], "symlink")
        self.assertEqual(skipped["file-link"], "symlink")
        self.assertEqual(skipped["node_modules"], "default_excluded")
        self.assertEqual(skipped["deep/__pycache__"], "default_excluded")
        self.assertEqual(skipped[".file-organization"], "default_excluded")
        self.assertNotIn(".DS_Store", skipped)
        self.assertTrue(report["complete"])

    def test_root_symlink_is_resolved(self) -> None:
        write(self.root / "real" / "a.txt", "a")
        os.symlink(self.root / "real", self.root / "alias")
        report = inventory.scan_inventory(self.root / "alias")
        self.assertEqual(report["root"], str(self.root / "real"))
        self.assertEqual(paths_of(report), ["a.txt"])

    def test_exclusion_semantics(self) -> None:
        write(self.root / "exports" / "big.csv", "x")
        write(self.root / "exports" / "nested" / "more.csv", "x")
        write(self.root / "keep" / "draft.tmp", "x")
        write(self.root / "keep" / "deep" / "other.tmp", "x")
        write(self.root / "中文 资料" / "会议 纪要.md", "纪要")
        write(self.root / "a b.txt", "x")

        report = inventory.scan_inventory(self.root, excludes=("exports", "*.tmp"))

        self.assertEqual(paths_of(report), ["a b.txt", "中文 资料/会议 纪要.md"])
        skipped = {item["path"]: item["reason"] for item in report["skipped"]}
        self.assertEqual(skipped["exports"], "excluded")
        self.assertEqual(skipped["keep/draft.tmp"], "excluded")
        self.assertEqual(skipped["keep/deep/other.tmp"], "excluded")
        self.assertNotIn("exports/big.csv", skipped)

    def test_exclusion_glob_with_double_star(self) -> None:
        write(self.root / "exports" / "a.csv", "x")
        write(self.root / "exports" / "sub" / "b.csv", "x")
        write(self.root / "kept.csv", "x")
        report = inventory.scan_inventory(self.root, excludes=("exports/**",))
        self.assertEqual(paths_of(report), ["kept.csv"])

    def test_partial_scan(self) -> None:
        write(self.root / "ok" / "a.txt", "a")
        write(self.root / "locked" / "b.txt", "b")
        real_scandir = os.scandir
        locked = str(self.root / "locked")

        def fake_scandir(path):
            if os.fspath(path) == locked:
                raise PermissionError(13, "Permission denied", locked)
            return real_scandir(path)

        with mock.patch.object(inventory.os, "scandir", side_effect=fake_scandir):
            report = inventory.scan_inventory(self.root)

        self.assertFalse(report["complete"])
        self.assertEqual(paths_of(report), ["ok/a.txt"])
        self.assertEqual(len(report["errors"]), 1)
        error = report["errors"][0]
        self.assertEqual(error["path"], "locked")
        self.assertEqual(error["kind"], "permission_denied")
        self.assertTrue(error["message"])

    def test_file_vanishes_during_scan(self) -> None:
        write(self.root / "a.txt", "a")
        write(self.root / "gone.txt", "g")
        real_lstat = os.lstat

        def fake_lstat(path, *args, **kwargs):
            if os.fspath(path).endswith("gone.txt"):
                raise FileNotFoundError(2, "No such file", os.fspath(path))
            return real_lstat(path, *args, **kwargs)

        with mock.patch.object(inventory.os, "lstat", side_effect=fake_lstat):
            report = inventory.scan_inventory(self.root)

        self.assertFalse(report["complete"])
        self.assertEqual(paths_of(report), ["a.txt"])
        self.assertEqual(report["errors"][0]["path"], "gone.txt")
        self.assertEqual(report["errors"][0]["kind"], "not_found")

    def test_scan_is_read_only(self) -> None:
        write(self.root / "a.txt", "abc")
        write(self.root / "b" / "c.txt", "abc")
        write(self.root / "repo" / "AGENTS.md", "x")
        os.symlink(self.root / "a.txt", self.root / "link")
        before = snapshot(self.root)

        inventory.scan_inventory(self.root, duplicates=True)
        with contextlib.redirect_stdout(io.StringIO()):
            inventory.main([str(self.root), "--duplicates", "--json"])
            inventory.main([str(self.root)])

        self.assertEqual(snapshot(self.root), before)

    def test_invalid_root_raises(self) -> None:
        with self.assertRaises(inventory.InvalidRootError):
            inventory.scan_inventory(self.root / "missing")
        write(self.root / "file.txt", "x")
        with self.assertRaises(inventory.InvalidRootError):
            inventory.scan_inventory(self.root / "file.txt")


class DuplicateTests(TempDirTestCase):
    def test_duplicates_disabled(self) -> None:
        write(self.root / "a.txt", "abc")
        write(self.root / "b.txt", "abc")
        with mock.patch.object(inventory, "_hash_stable_file") as hasher:
            report = inventory.scan_inventory(self.root)
        hasher.assert_not_called()
        self.assertEqual(report["duplicate_groups"], [])
        self.assertIsNone(report["summary"]["estimated_reclaimable_bytes"])

    def test_duplicate_content_not_name(self) -> None:
        write(self.root / "a" / "x.txt", "abc")
        write(self.root / "b" / "y.txt", "abc")
        write(self.root / "c" / "x.txt", "xyz")

        report = inventory.scan_inventory(self.root, duplicates=True)

        self.assertTrue(report["complete"])
        self.assertEqual(len(report["duplicate_groups"]), 1)
        group = report["duplicate_groups"][0]
        self.assertEqual(set(group), {"size", "sha256", "paths"})
        self.assertEqual(group["paths"], ["a/x.txt", "b/y.txt"])
        self.assertEqual(group["size"], 3)
        self.assertEqual(len(group["sha256"]), 64)
        self.assertEqual(report["summary"]["estimated_reclaimable_bytes"], 3)

    def test_hardlinks_not_extra_copies(self) -> None:
        write(self.root / "orig.txt", "abc")
        os.link(self.root / "orig.txt", self.root / "link.txt")

        report = inventory.scan_inventory(self.root, duplicates=True)
        self.assertEqual(report["duplicate_groups"], [])
        self.assertEqual(report["summary"]["estimated_reclaimable_bytes"], 0)
        self.assertEqual(len(report["hardlink_groups"]), 1)
        self.assertEqual(report["hardlink_groups"][0]["paths"], ["link.txt", "orig.txt"])

        write(self.root / "copy.txt", "abc")
        report = inventory.scan_inventory(self.root, duplicates=True)
        self.assertEqual(len(report["duplicate_groups"]), 1)
        self.assertEqual(
            report["duplicate_groups"][0]["paths"], ["copy.txt", "link.txt", "orig.txt"]
        )
        self.assertEqual(report["summary"]["estimated_reclaimable_bytes"], 3)

    def test_empty_duplicates(self) -> None:
        write(self.root / "empty1", "")
        write(self.root / "empty2", "")
        report = inventory.scan_inventory(self.root, duplicates=True)
        self.assertEqual(len(report["duplicate_groups"]), 1)
        self.assertEqual(report["duplicate_groups"][0]["size"], 0)
        self.assertEqual(report["summary"]["estimated_reclaimable_bytes"], 0)

    def test_no_hash_for_unique_sizes(self) -> None:
        write(self.root / "a.txt", "a")
        write(self.root / "b.txt", "bb")
        write(self.root / "c.txt", "ccc")
        with mock.patch.object(inventory, "_hash_stable_file") as hasher:
            report = inventory.scan_inventory(self.root, duplicates=True)
        hasher.assert_not_called()
        self.assertEqual(report["duplicate_groups"], [])
        self.assertEqual(report["summary"]["estimated_reclaimable_bytes"], 0)

    def test_changed_during_hash(self) -> None:
        write(self.root / "a.txt", "abc")
        write(self.root / "b.txt", "abc")
        write(self.root / "c.txt", "abc")
        real_hash = inventory._hash_stable_file

        def mutate_then_hash(path):
            if path.name == "b.txt":
                with open(path, "a", encoding="utf-8") as handle:
                    handle.write("changed")
            return real_hash(path)

        with mock.patch.object(inventory, "_hash_stable_file", side_effect=mutate_then_hash):
            report = inventory.scan_inventory(self.root, duplicates=True)

        self.assertFalse(report["complete"])
        self.assertEqual(report["errors"][0]["path"], "b.txt")
        self.assertEqual(report["errors"][0]["kind"], "changed_during_scan")
        self.assertEqual(report["duplicate_groups"][0]["paths"], ["a.txt", "c.txt"])
        self.assertEqual(report["summary"]["estimated_reclaimable_bytes"], 3)

    def test_hash_detects_mid_read_change(self) -> None:
        target = write(self.root / "a.bin", b"x" * 10)
        real_sha256 = inventory.hashlib.sha256

        class MutatingHash:
            def __init__(self) -> None:
                self._inner = real_sha256()
                self._done = False

            def update(self, data: bytes) -> None:
                if not self._done:
                    self._done = True
                    with open(target, "ab") as handle:
                        handle.write(b"more")
                self._inner.update(data)

            def hexdigest(self) -> str:
                return self._inner.hexdigest()

        with mock.patch.object(inventory.hashlib, "sha256", MutatingHash):
            with self.assertRaises(inventory.FileChangedError):
                inventory._hash_stable_file(target)

    def test_unreadable_candidate(self) -> None:
        write(self.root / "a.txt", "abc")
        write(self.root / "b.txt", "abc")
        write(self.root / "x.txt", "wxyz")
        write(self.root / "y.txt", "wxyz")
        real_hash = inventory._hash_stable_file

        def deny_b(path):
            if path.name == "b.txt":
                raise PermissionError(13, "Permission denied", str(path))
            return real_hash(path)

        with mock.patch.object(inventory, "_hash_stable_file", side_effect=deny_b):
            report = inventory.scan_inventory(self.root, duplicates=True)

        self.assertFalse(report["complete"])
        self.assertEqual(report["errors"][0]["path"], "b.txt")
        self.assertEqual(report["errors"][0]["kind"], "permission_denied")
        self.assertEqual(
            [group["paths"] for group in report["duplicate_groups"]], [["x.txt", "y.txt"]]
        )
        self.assertEqual(report["summary"]["estimated_reclaimable_bytes"], 4)

    def test_unreadable_hardlink_excludes_all_its_paths(self) -> None:
        write(self.root / "a.txt", "abc")
        os.link(self.root / "a.txt", self.root / "a-link.txt")
        write(self.root / "b.txt", "abc")
        real_hash = inventory._hash_stable_file

        def deny_a(path):
            if path.name in {"a.txt", "a-link.txt"}:
                raise PermissionError(13, "Permission denied", str(path))
            return real_hash(path)

        with mock.patch.object(inventory, "_hash_stable_file", side_effect=deny_a):
            report = inventory.scan_inventory(self.root, duplicates=True)

        self.assertEqual(report["duplicate_groups"], [])
        self.assertEqual(report["summary"]["estimated_reclaimable_bytes"], 0)


class CliTests(TempDirTestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = inventory.main(list(args))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_json_valid_root(self) -> None:
        write(self.root / "a.txt", "abc")
        code, out, _ = self.run_cli(str(self.root), "--json")
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(report["summary"]["file_count"], 1)
        self.assertEqual(report["duplicate_groups"], [])

    def test_json_duplicates(self) -> None:
        write(self.root / "a.txt", "abc")
        write(self.root / "b.txt", "abc")
        code, out, _ = self.run_cli(str(self.root), "--duplicates", "--json")
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(report["duplicate_groups"][0]["paths"], ["a.txt", "b.txt"])
        self.assertEqual(report["summary"]["estimated_reclaimable_bytes"], 3)

    def test_json_exclude_repeatable(self) -> None:
        write(self.root / "a.txt", "a")
        write(self.root / "b.tmp", "b")
        write(self.root / "exports" / "c.csv", "c")
        code, out, _ = self.run_cli(
            str(self.root), "--exclude", "*.tmp", "--exclude", "exports", "--json"
        )
        self.assertEqual(code, 0)
        self.assertEqual(paths_of(json.loads(out)), ["a.txt"])

    def test_invalid_root_json(self) -> None:
        code, out, _ = self.run_cli(str(self.root / "missing"), "--json")
        self.assertEqual(code, 2)
        report = json.loads(out)
        self.assertFalse(report["complete"])
        self.assertEqual(report["errors"][0]["kind"], "invalid_root")
        self.assertEqual(report["files"], [])

    def test_invalid_root_text(self) -> None:
        code, out, err = self.run_cli(str(self.root / "missing"))
        self.assertEqual(code, 2)
        self.assertIn("invalid_root", out + err)

    def test_partial_scan_exit_code(self) -> None:
        write(self.root / "locked" / "a.txt", "a")
        real_scandir = os.scandir
        locked = str(self.root / "locked")

        def fake_scandir(path):
            if os.fspath(path) == locked:
                raise PermissionError(13, "Permission denied", locked)
            return real_scandir(path)

        with mock.patch.object(inventory.os, "scandir", side_effect=fake_scandir):
            code, out, _ = self.run_cli(str(self.root), "--json")
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["complete"])

    def test_bad_argument_uses_argparse(self) -> None:
        code, out, err = self.run_cli("--no-such-flag")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("usage", err)

    def test_help_lists_options(self) -> None:
        code, out, _ = self.run_cli("--help")
        self.assertEqual(code, 0)
        for flag in ("--json", "--duplicates", "--exclude"):
            self.assertIn(flag, out)

    def test_text_output_uses_same_report(self) -> None:
        write(self.root / "small.txt", "a")
        write(self.root / "big.bin", "x" * 100)
        report = inventory.scan_inventory(self.root)
        text = inventory.render_text(report)
        self.assertIn(str(self.root), text)
        self.assertIn("big.bin", text)
        self.assertLess(text.index("big.bin"), text.index("small.txt"))
        code, out, _ = self.run_cli(str(self.root))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), text.strip())

    def test_text_output_lists_at_most_ten_largest(self) -> None:
        for index in range(12):
            write(self.root / f"f{index:02d}.txt", "x" * (index + 1))
        text = inventory.render_text(inventory.scan_inventory(self.root))
        self.assertIn("f11.txt", text)
        self.assertNotIn("f00.txt", text)
        self.assertNotIn("f01.txt", text)


if __name__ == "__main__":
    unittest.main()
