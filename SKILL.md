---
name: stock-report-downloader
description: Use when working in this repository or when a user asks to download, verify, or troubleshoot A-share and HK stock financial reports with the local downloader. Trigger this skill for tasks such as running the existing CLI, validating stock-name resolution, checking language selection, verifying known report examples, or fixing cninfo/HKEX downloader behavior instead of rebuilding the workflow from scratch.
---

# Stock Report Downloader

Use the existing downloader implementation in this repository instead of writing one-off scraping code.

## Workflow

1. Work from the repository root that contains `pyproject.toml`, `uv.lock`, and `scripts/report_downloader/`.
2. Use `uv run stock-report-downloader ...` for normal invocations.
3. Use `python scripts/run_report.py ...` when you want a stable wrapper script from the skill root.
4. Use `python scripts/verify_examples.py --list` to inspect built-in verification cases before running one.
5. For Chinese stock names with market ambiguity, set `--market hk` for Hong Kong stocks.
6. Keep downloads in a user-specified directory, or use `./test_output` for verification runs.

## What To Check First

- Read `references/usage.md` for tested commands, expected behavior, and known limitations.
- Inspect the existing modules before changing behavior:
  - `scripts/report_downloader/cli.py`
  - `scripts/report_downloader/stock_search.py`
  - `scripts/report_downloader/downloader_cninfo.py`
  - `scripts/report_downloader/downloader_hkex.py`
- Keep changes aligned with the existing `uv` workflow in `pyproject.toml` and `uv.lock`.

## Guardrails

- Do not bypass the CLI and call cninfo/HKEX endpoints directly unless you are debugging or patching the downloader.
- Preserve the existing filename convention unless the user explicitly asks to change it.
- Prefer fixing the existing downloader modules over writing ad hoc scripts outside `scripts/`.
- Treat `references/usage.md` as the source of truth for verified example commands.
