"""Machine-specific settings, read from the environment or from .env at the repository root.

  VTK_REPO              a VTK clone with the upstream remote fetched (default: ../vtk beside this repository)
  OLLAMA_HOST           Ollama server for local models and embeddings (default: http://localhost:11434)
  VTK_REVIEW_WORKTREE   scratch worktree for the developer checks (default: ../vtk-review-wt)
  VTK_REVIEW_BUILD      build directory for the developer checks (default: ../vtk-review-build)

Relative paths are taken from the repository root. See .env.example.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _load_env():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        name, sep, value = line.partition("=")
        name = name.strip()
        if sep and name and not name.startswith("#"):
            os.environ.setdefault(name, value.strip().strip("'\""))


def _path(name, default):
    value = Path(os.environ.get(name, default))
    return str(value if value.is_absolute() else (ROOT / value).resolve())


_load_env()
VTK_REPO = _path("VTK_REPO", "../vtk")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
WORKTREE = _path("VTK_REVIEW_WORKTREE", "../vtk-review-wt")
BUILD = _path("VTK_REVIEW_BUILD", "../vtk-review-build")
