#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


EXAMPLES: dict[str, list[str]] = {
    "a-code": ["000001", "-t", "annual", "-y", "2024", "-o", "./test_output"],
    "a-name": ["平安银行", "-t", "annual", "-y", "2024", "-o", "./test_output"],
    "hk-code": ["06049", "-t", "annual", "-y", "2023", "-m", "hk", "-o", "./test_output"],
    "hk-name": ["保利物业", "-t", "annual", "-y", "2023", "-m", "hk", "-o", "./test_output"],
    "hk-en": ["06049", "-t", "annual", "-y", "2023", "-m", "hk", "-l", "en", "-o", "./test_output"],
    "error": ["999999", "-t", "annual", "-y", "2024"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run built-in verification examples for the stock report downloader.")
    parser.add_argument("example", nargs="?", choices=sorted(EXAMPLES), help="Example name to run")
    parser.add_argument("--list", action="store_true", help="List available examples")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.list:
        for name in sorted(EXAMPLES):
            print(name)
        return 0
    if not args.example:
        raise SystemExit("Provide an example name or use --list.")

    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.setdefault("UV_CACHE_DIR", str(repo_root / ".uv-cache"))
    command = ["uv", "run", "stock-report-downloader", *EXAMPLES[args.example]]
    return subprocess.run(command, cwd=repo_root, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
