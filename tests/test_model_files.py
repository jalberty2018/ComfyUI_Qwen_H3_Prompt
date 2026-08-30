from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "qwen_h3_model_files_under_test",
    PROJECT_ROOT / "model_files.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load model_files.py for testing.")
model_files = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = model_files
SPEC.loader.exec_module(model_files)


class ModelFileResolutionTests(unittest.TestCase):
    def test_legacy_workflow_name_uses_provisioned_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            provisioned = root / model_files.DEFAULT_MODEL
            provisioned.parent.mkdir(parents=True)
            provisioned.write_bytes(b"test")

            resolved = model_files.resolve_gguf(root, "Qwen3.8-27B-Q4_K_M.gguf")

            self.assertEqual(resolved, provisioned.resolve())

    def test_existing_requested_model_takes_precedence_over_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            requested = root / "Qwen3.8-27B-Q4_K_M.gguf"
            requested.write_bytes(b"requested")
            replacement = root / model_files.DEFAULT_MODEL
            replacement.parent.mkdir(parents=True)
            replacement.write_bytes(b"replacement")

            resolved = model_files.resolve_gguf(root, requested.name)

            self.assertEqual(resolved, requested.resolve())

    def test_missing_legacy_model_reports_compatible_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, model_files.DEFAULT_MODEL):
                model_files.resolve_gguf(Path(directory), "Qwen3.8-27B-Q4_K_M.gguf")

    def test_path_outside_model_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                model_files.resolve_gguf(Path(directory), "../outside.gguf")

    def test_bare_legacy_filename_resolves_in_nested_model_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dolphin = root / "Dolphin-Mistral-24B-Venice-Edition-heretic"
            dolphin.mkdir()
            model = dolphin / "Dolphin-Mistral-24B-Venice-Edition-heretic.Q4_K_M.gguf"
            model.write_bytes(b"model")

            resolved = model_files.resolve_gguf(root, model.name)

            self.assertEqual(resolved, model.resolve())

    def test_recursive_options_separate_models_and_projectors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dolphin = root / "Dolphin-Mistral-24B-Venice-Edition-heretic"
            dolphin.mkdir()
            model_name = "Dolphin-Mistral-24B-Venice-Edition-heretic.Q4_K_M.gguf"
            projector_name = "Dolphin-Mistral-24B-Venice-Edition-heretic.mmproj-Q8_0.gguf"
            (dolphin / model_name).write_bytes(b"model")
            (dolphin / projector_name).write_bytes(b"projector")
            cache = dolphin / ".cache"
            cache.mkdir()
            (cache / "ignored.gguf").write_bytes(b"cache")

            self.assertEqual(
                model_files.gguf_options(root, projector=False),
                [f"{dolphin.name}/{model_name}"],
            )
            self.assertEqual(
                model_files.gguf_options(root, projector=True),
                [f"{dolphin.name}/{projector_name}"],
            )


if __name__ == "__main__":
    unittest.main()
