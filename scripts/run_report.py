#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.setdefault("UV_CACHE_DIR", str(repo_root / ".uv-cache"))
    command = ["uv", "run", "stock-report-downloader", *sys.argv[1:]]
    return subprocess.run(command, cwd=repo_root, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
