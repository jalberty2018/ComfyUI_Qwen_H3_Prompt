from __future__ import annotations

import logging
from pathlib import Path


DEFAULT_MODEL = "Qwen3.8/qwen3.8-27b-uncensored-fp8-q4_k_m.gguf"
DEFAULT_MMPROJ = "Qwen3.8/mmproj-F16.gguf"
MODEL_FILENAME_ALIASES = {
    "Qwen3.8-27B-Q4_K_M.gguf": DEFAULT_MODEL,
}


def _is_usable_gguf(path: Path, root: Path) -> bool:
    return (
        path.is_file()
        and path.suffix.lower() == ".gguf"
        and path.is_relative_to(root)
        and ".cache" not in path.relative_to(root).parts
    )


def gguf_options(model_root: Path, projector: bool) -> list[str]:
    root = model_root.resolve()
    if not root.is_dir():
        return []
    options = []
    for path in root.rglob("*.gguf"):
        resolved = path.resolve()
        if not _is_usable_gguf(resolved, root):
            continue
        is_projector = "mmproj" in path.name.lower()
        if is_projector == projector:
            options.append(resolved.relative_to(root).as_posix())
    return sorted(options, key=str.casefold)


def resolve_gguf(model_dir: Path, name: str, logger: logging.Logger | None = None) -> Path:
    root = model_dir.resolve()
    replacement = MODEL_FILENAME_ALIASES.get(name)
    candidates = (name, replacement) if replacement else (name,)
    for candidate in candidates:
        path = (root / candidate).resolve()
        if _is_usable_gguf(path, root):
            if candidate != name and logger is not None:
                logger.warning(
                    "[Qwen H3] Model filename %s is unavailable; using provisioned replacement %s",
                    name,
                    candidate,
                )
            return path

        # Older workflows stored only a filename because the node previously
        # searched one fixed Qwen3.8 directory. Resolve that filename anywhere
        # below models/LLM when it has one unambiguous match.
        if Path(candidate).name == candidate and root.is_dir():
            matches = [
                match.resolve()
                for match in root.rglob(candidate)
                if _is_usable_gguf(match.resolve(), root)
            ]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                relative_matches = ", ".join(
                    match.relative_to(root).as_posix() for match in matches
                )
                raise FileNotFoundError(
                    f"Ambiguous GGUF filename in {root}: {candidate}; choose one of: {relative_matches}"
                )
    replacement_hint = f"; compatible replacement: {replacement}" if replacement else ""
    raise FileNotFoundError(
        f"Invalid or missing GGUF model in {root}: {name}{replacement_hint}"
    )
