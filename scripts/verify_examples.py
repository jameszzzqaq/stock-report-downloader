#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.28.0",
# ]
# ///
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_downloader.cli import main as run_downloader


EXAMPLES: dict[str, dict[str, object]] = {
    "a-code": {
        "command": ["000001", "-t", "annual", "-y", "2024", "-o", "./test_output"],
        "expected": "Download Ping An Bank 2024 annual report PDF into ./test_output.",
    },
    "a-name": {
        "command": ["平安银行", "-t", "annual", "-y", "2024", "-o", "./test_output"],
        "expected": "Resolve to 000001 and download the same 2024 annual report PDF.",
    },
    "hk-code": {
        "command": ["06049", "-t", "annual", "-y", "2023", "-m", "hk", "-o", "./test_output"],
        "expected": "Download Poly Property Services 2023 annual report in Chinese.",
    },
    "hk-name": {
        "command": ["保利物业", "-t", "annual", "-y", "2023", "-m", "hk", "-o", "./test_output"],
        "expected": "Resolve to 06049 and download the same 2023 annual report PDF.",
    },
    "hk-en": {
        "command": ["06049", "-t", "annual", "-y", "2023", "-m", "hk", "-l", "en", "-o", "./test_output"],
        "expected": "Download the English 2023 annual report when HKEX provides one.",
    },
    "error": {
        "command": ["999999", "-t", "annual", "-y", "2024"],
        "expected": "Exit non-zero and report that no matching report was found.",
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run built-in verification examples for the stock report downloader.")
    parser.add_argument("example", nargs="?", choices=sorted(EXAMPLES), help="Example name to run")
    parser.add_argument("--list", action="store_true", help="List available examples")
    parser.add_argument("--details", action="store_true", help="Show expected outcome when listing examples")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.list:
        for name in sorted(EXAMPLES):
            print(name)
            if args.details:
                print(f"  expected: {EXAMPLES[name]['expected']}")
        return 0
    if not args.example:
        raise SystemExit("Provide an example name or use --list.")
    return run_downloader(list(EXAMPLES[args.example]["command"]))


if __name__ == "__main__":
    raise SystemExit(main())
