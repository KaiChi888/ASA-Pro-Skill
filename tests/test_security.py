import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


broad = load_script("broad_to_exact", "skills/asa-pro/scripts/broad_to_exact.py")
research = load_script("app_store_relevance", "skills/asa-pro/scripts/app_store_relevance.py")


class SecurityTests(unittest.TestCase):
    def test_cli_error_secret_redaction(self):
        synthetic = (
            "Authorization: Bearer " + "A" * 32
            + "\nAuthorization: " + "*" * 24
            + "\napi_key=" + "B" * 32
            + "\nsk-" + "C" * 24
            + "\nSEARCHADS." + "D" * 24
            + "\nclient_id=" + "E" * 24
        )
        output = broad.redact_secrets(synthetic)
        for marker in ("A", "B", "C", "D", "E"):
            self.assertNotIn(marker * 16, output)
        self.assertNotIn("*" * 16, output)
        self.assertGreaterEqual(output.count("[REDACTED]"), 6)
        self.assertNotIn("E" * 16, research.redact_secrets("client_id=" + "E" * 24))

    def test_state_is_mode_0600_and_destination_symlink_is_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            broad.secure_write_text(state, "{}\n")
            self.assertEqual(stat.S_IMODE(state.stat().st_mode), 0o600)

            target = Path(directory) / "target"
            target.write_text("unchanged")
            state.unlink()
            state.symlink_to(target)
            broad.secure_write_text(state, "changed")
            self.assertEqual(target.read_text(), "unchanged")
            self.assertFalse(state.is_symlink())
            self.assertEqual(state.read_text(), "changed")
            self.assertEqual(stat.S_IMODE(state.stat().st_mode), 0o600)

    def test_research_output_is_mode_0600_and_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "research.json"
            research.secure_write_text(output, "{}\n")
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            output.unlink()
            target = Path(directory) / "target"
            target.write_text("unchanged")
            output.symlink_to(target)
            with self.assertRaises(OSError):
                research.secure_write_text(output, "changed")
            self.assertEqual(target.read_text(), "unchanged")

    def test_single_instance_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "run.lock"
            first = broad.acquire_lock(lock_path)
            try:
                with self.assertRaises(RuntimeError):
                    broad.acquire_lock(lock_path)
            finally:
                first.close()
            second = broad.acquire_lock(lock_path)
            second.close()
            self.assertEqual(stat.S_IMODE(lock_path.stat().st_mode), 0o600)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
    def test_lock_symlink_is_rejected_without_changing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.write_text("unchanged")
            os.chmod(target, 0o644)
            lock_path = Path(directory) / "run.lock"
            lock_path.symlink_to(target)
            with self.assertRaises(OSError):
                broad.acquire_lock(lock_path)
            self.assertEqual(target.read_text(), "unchanged")
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o644)

    def test_main_releases_lock_after_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "run.lock"
            with patch.object(broad, "parse_args", return_value=SimpleNamespace(lock_file=lock_path)):
                with patch.object(broad, "run", side_effect=RuntimeError("synthetic failure")):
                    with self.assertRaises(RuntimeError):
                        broad.main()
            handle = broad.acquire_lock(lock_path)
            handle.close()

    def test_top_level_initialization_error_is_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            secret = "E" * 24
            approval = Path(directory) / f"client_id={secret}.json"
            script = ROOT / "skills/asa-pro/scripts/broad_to_exact.py"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--apply",
                    "--campaign-name-prefix",
                    "Demo -",
                    "--aads-bin",
                    "/bin/true",
                    "--relevance-file",
                    str(approval),
                    "--state",
                    str(Path(directory) / "state.json"),
                    "--lock-file",
                    str(Path(directory) / "run.lock"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(secret, result.stderr)
            self.assertIn("[REDACTED]", result.stderr)


if __name__ == "__main__":
    unittest.main()
