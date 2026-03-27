# Usage Reference

## Run Commands

Run from the repository root.

```bash
uv sync
uv run stock-report-downloader --help
```

Use the CLI for normal work:

```bash
uv run stock-report-downloader STOCK --type TYPE --year YEAR [options]
```

Use the wrapper script only for debugging or script-oriented workflows:

```bash
uv run python scripts/run_report.py STOCK --type TYPE --year YEAR [options]
```

Run deterministic offline checks before hitting live sources:

```bash
uv run python -m unittest discover -s tests -v
uv run python scripts/verify_examples.py --list --details
```

## Verified Commands

Verification template:

- Last verified live cases: `2026-03-27`
- Verifier: `Codex`
- Output root used during verification: `./test_output` or another explicit temporary directory
- If you change a verified command, update the date and expected result together.

A-share by code:
Expected result: download Ping An Bank 2024 annual report PDF into `./test_output`.

```bash
uv run stock-report-downloader 000001 -t annual -y 2024 -o ./test_output
```

A-share by name:
Expected result: resolve to `000001` and download the same 2024 annual report PDF.

```bash
uv run stock-report-downloader 平安银行 -t annual -y 2024 -o ./test_output
```

HK stock by code:
Expected result: download Poly Property Services 2023 annual report in Chinese.

```bash
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -o ./test_output
```

HK stock by simplified Chinese name:
Expected result: resolve to `06049` and download the same 2023 annual report PDF.

```bash
uv run stock-report-downloader 保利物业 -t annual -y 2023 -m hk -o ./test_output
```

HK stock with English preference:
Expected result: download the English 2023 annual report when HKEX provides one.

```bash
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -l en -o ./test_output
```

Error handling check:
Expected result: exit non-zero and report that no matching report was found.

```bash
uv run stock-report-downloader 999999 -t annual -y 2024
```

## Current Behavior

- A-share reports use cninfo.
- HK reports use HKEX `partial.do` plus `titleSearchServlet.do`.
- Annual reports search across the next filing year to catch next-year disclosures.
- Output filenames include stock code and stock name.
- HK simplified Chinese names use a lightweight local simplified-to-traditional fallback.

## Known Limitations

- HK simplified-name compatibility is not full OpenCC-grade conversion.
- Some HK issuers only publish one language version PDF; `--lang` only changes selection priority.
- External site structure changes may require updates in the downloader modules.

## Troubleshooting Map

- Name resolution problems: `scripts/report_downloader/stock_search.py`
- cninfo report matching problems: `scripts/report_downloader/downloader_cninfo.py`
- HKEX lookup or language-selection problems: `scripts/report_downloader/downloader_hkex.py`
- Download validation or network error problems: `scripts/report_downloader/utils.py`
- CLI invocation issues: `scripts/report_downloader/cli.py`

## Files To Inspect When Fixing Issues

- `scripts/report_downloader/cli.py`
- `scripts/report_downloader/stock_search.py`
- `scripts/report_downloader/downloader_cninfo.py`
- `scripts/report_downloader/downloader_hkex.py`
- `pyproject.toml`
- `uv.lock`
