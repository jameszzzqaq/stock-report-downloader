---
name: stock-report-downloader
description: Use when working in this repository or when a user asks to download, verify, or troubleshoot A-share and HK stock financial reports with the local downloader. Trigger this skill for tasks such as running the existing CLI, validating stock-name resolution, checking language selection, verifying known report examples, or fixing cninfo/HKEX downloader behavior instead of rebuilding the workflow from scratch.
---

# Stock Report Downloader

Use the existing downloader implementation in this repository instead of writing one-off scraping code.

## Inputs

- Required user inputs:
  - `stock`: stock code or company name.
  - `--type`: one of `annual`, `semi`, `q1`, `q3`.
  - `--year`: report year.
- Optional but sometimes required:
  - `--market hk` when a Chinese company name could refer to a Hong Kong issuer.
  - `--lang` only matters for HK reports and only changes selection priority.
  - `--output` when the user wants files in a specific directory.
- Ambiguity handling:
  - If the user gives a numeric code, prefer the code directly.
  - If the user gives a Chinese company name and it might be a Hong Kong issuer, prefer asking for or setting `--market hk` explicitly instead of guessing.
  - If required inputs are missing, gather them before running the downloader.

## Workflow

1. Work from the repository root that contains `pyproject.toml`, `uv.lock`, and `scripts/report_downloader/`.
2. Use `uv run stock-report-downloader ...` as the primary entrypoint for all normal work.
3. Use `uv run python scripts/run_report.py ...` only when you specifically need the wrapper script for debugging or scripting from the skill root.
4. Use `uv run python scripts/verify_examples.py --list --details` only to inspect or replay built-in live examples.
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

## Verification Order

1. Run deterministic offline checks first:
   - `uv run python -m unittest discover -s tests -v`
2. Inspect built-in live examples before choosing one:
   - `uv run python scripts/verify_examples.py --list --details`
3. Run a real downloader example only when you need end-to-end validation against cninfo or HKEX.
4. When updating `references/usage.md`, re-run the affected example and record the current verification date and expected outcome.

## Troubleshooting

- A-share name or code resolution issues:
  - inspect `scripts/report_downloader/stock_search.py`
  - name search no longer accepts the first unrelated candidate; prefer an exact name or `--market`
- cninfo query returns no report or the wrong announcement:
  - inspect `scripts/report_downloader/downloader_cninfo.py`
- HKEX security lookup, language selection, or title filtering issues:
  - inspect `scripts/report_downloader/downloader_hkex.py`
  - quarterly reports need first/third-quarter wording, not a generic quarterly title
- Download succeeds but content is not a valid PDF, or network errors are unclear:
  - inspect `scripts/report_downloader/utils.py`
- CLI argument handling or end-user invocation behavior:
  - inspect `scripts/report_downloader/cli.py`

## Guardrails

- Do not bypass the CLI and call cninfo/HKEX endpoints directly unless you are debugging or patching the downloader.
- Preserve the existing filename convention unless the user explicitly asks to change it.
- Prefer fixing the existing downloader modules over writing ad hoc scripts outside `scripts/`.
- Treat `references/usage.md` as the source of truth for verified example commands.
- Prefer the primary CLI entrypoint over wrapper scripts unless there is a concrete reason to use the wrapper.
