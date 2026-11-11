from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "qwen_h3_runtime_under_test",
    PROJECT_ROOT / "runtime.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load runtime.py for testing.")
runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)


class ExternalRuntimeTests(unittest.TestCase):
    def test_external_llama_server_overrides_missing_bundled_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / (
                "llama-server.exe" if os.name == "nt" else "llama-server"
            )
            executable.write_bytes(b"test")
            executable.chmod(0o755)
            with patch.dict(
                os.environ,
                {runtime.EXTERNAL_LLAMA_SERVER_ENV: str(executable)},
                clear=False,
            ):
                spec = runtime.load_runtime_spec(root=Path(directory))

        self.assertEqual(spec.executable, executable.resolve())
        self.assertEqual(spec.library_dirs, ())
        self.assertEqual(
            spec.backend,
            f"external ({runtime.EXTERNAL_LLAMA_SERVER_ENV})",
        )

    def test_external_llama_server_must_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing-qwen-h3-llama-server"
            with patch.dict(
                os.environ,
                {runtime.EXTERNAL_LLAMA_SERVER_ENV: str(missing)},
                clear=False,
            ):
                with self.assertRaisesRegex(RuntimeError, "does not point to"):
                    runtime.load_runtime_spec()

    def test_empty_library_dirs_leave_environment_unchanged(self):
        spec = runtime.RuntimeSpec(
            executable=Path("/opt/llama.cpp/bin/llama-server"),
            library_dirs=(),
            platform_name="linux",
            backend="external",
            n_gpu_layers="auto",
            fit=True,
            fit_target_mib=1536,
            flash_attention="auto",
        )
        original = {"PATH": "original-path", "LD_LIBRARY_PATH": "original-libs"}
        self.assertEqual(runtime.build_runtime_environment(spec, original), original)


class MtpTests(unittest.TestCase):
    def test_auto_fallback_is_reused_and_mode_change_restarts(self):
        spec = MagicMock()
        first, fallback, disabled = MagicMock(), MagicMock(), MagicMock()
        first.start.side_effect = RuntimeError("MTP unsupported")
        with patch.object(runtime, "load_runtime_spec", return_value=spec), patch.object(
            runtime, "LlamaServer", side_effect=[first, fallback, disabled]
        ) as factory:
            manager = runtime.LlamaServerManager()
            model, projector = Path("model.gguf"), Path("mmproj.gguf")
            server, fresh = manager.acquire(model, projector, mtp="auto")
            self.assertIs(server, fallback)
            self.assertTrue(fresh)
            first.stop.assert_called_once()
            self.assertEqual(factory.call_args.kwargs["mtp"], "off")
            self.assertEqual(manager.acquire(model, projector, mtp="auto"), (fallback, False))
            self.assertEqual(manager.acquire(model, projector, mtp="off"), (disabled, True))
            fallback.stop.assert_called_once()
            manager.release()

    def test_explicit_on_propagates_failure(self):
        server = MagicMock()
        server.start.side_effect = RuntimeError("MTP unsupported")
        with patch.object(runtime, "load_runtime_spec"), patch.object(
            runtime, "LlamaServer", return_value=server
        ) as factory:
            with self.assertRaisesRegex(RuntimeError, "MTP unsupported"):
                runtime.LlamaServerManager().acquire(Path("m"), Path("p"), mtp="on")
            self.assertEqual(factory.call_count, 1)
            server.stop.assert_called_once()

    def test_start_passes_mtp_only_when_enabled(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "llama-server"
            executable.touch()
            spec = runtime.RuntimeSpec(executable, (), "linux", "test", "auto", False, 1536, "auto")
            for mode in ("auto", "on", "off"):
                server = runtime.LlamaServer(Path("m"), Path("p"), runtime_spec=spec, mtp=mode)
                with patch.object(runtime.subprocess, "Popen") as process, patch.object(server, "_request"):
                    process.return_value.poll.return_value = None
                    try:
                        server.start()
                        args = process.call_args.args[0]
                        self.assertEqual("--spec-type" in args, mode != "off")
                        if mode != "off":
                            self.assertEqual(args[args.index("--spec-type") + 1], "draft-mtp")
                    finally:
                        server.stop()


if __name__ == "__main__":
    unittest.main()
