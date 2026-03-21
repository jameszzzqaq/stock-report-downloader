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

Use the wrapper script when you want a stable script entrypoint:

```bash
python scripts/run_report.py STOCK --type TYPE --year YEAR [options]
```

## Verified Commands

A-share by code:

```bash
uv run stock-report-downloader 000001 -t annual -y 2024 -o ./test_output
```

A-share by name:

```bash
uv run stock-report-downloader 平安银行 -t annual -y 2024 -o ./test_output
```

HK stock by code:

```bash
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -o ./test_output
```

HK stock by simplified Chinese name:

```bash
uv run stock-report-downloader 保利物业 -t annual -y 2023 -m hk -o ./test_output
```

HK stock with English preference:

```bash
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -l en -o ./test_output
```

Error handling check:

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

## Files To Inspect When Fixing Issues

- `scripts/report_downloader/cli.py`
- `scripts/report_downloader/stock_search.py`
- `scripts/report_downloader/downloader_cninfo.py`
- `scripts/report_downloader/downloader_hkex.py`
- `pyproject.toml`
- `uv.lock`
