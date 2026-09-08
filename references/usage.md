# Usage Reference

Run every command from the skill root (the directory that contains `SKILL.md`).

## Run Commands

Preferred entrypoint (self-contained, works after the skill is copied into any agent's skills folder):

```bash
uv run scripts/run_report.py --help
uv run scripts/run_report.py STOCK --type TYPE --year YEAR --output OUTPUT_DIR
```

If `uv` is unavailable:

```bash
python3 -m pip install -q "requests>=2.28.0"
python3 scripts/run_report.py STOCK --type TYPE --year YEAR --output OUTPUT_DIR
```

Always pass `--output`. The CLI default is the current directory.

Offline checks before live downloads:

```bash
uv run python -m unittest discover -s tests -v
uv run scripts/verify_examples.py --list --details
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
uv run scripts/run_report.py 000001 -t annual -y 2024 -o ./test_output
```

A-share by name:
Expected result: resolve to `000001` and download the same 2024 annual report PDF.

```bash
uv run scripts/run_report.py 平安银行 -t annual -y 2024 -o ./test_output
```

HK stock by code:
Expected result: download Poly Property Services 2023 annual report in Chinese.

```bash
uv run scripts/run_report.py 06049 -t annual -y 2023 -m hk -o ./test_output
```

HK stock by simplified Chinese name:
Expected result: resolve to `06049` and download the same 2023 annual report PDF.

```bash
uv run scripts/run_report.py 保利物业 -t annual -y 2023 -m hk -o ./test_output
```

HK stock with English preference:
Expected result: download the English 2023 annual report when HKEX provides one.

```bash
uv run scripts/run_report.py 06049 -t annual -y 2023 -m hk -l en -o ./test_output
```

Error handling check:
Expected result: exit non-zero and report that no matching report was found.

```bash
uv run scripts/run_report.py 999999 -t annual -y 2024
```

## Current Behavior

- A-share reports use cninfo.
- HK reports use HKEX `partial.do` plus `titleSearchServlet.do`.
- Annual reports search across the next filing year to catch next-year disclosures.
- Output filenames include stock code and stock name.
- HK simplified Chinese names use a lightweight local simplified-to-traditional fallback.
- Name search prefers an exact name or code match, then a substring match. It does not fall back to the first unrelated search hit.
- HK quarterly matching requires first/third-quarter wording. A generic "quarterly report" title is not enough.

## Known Limitations

- HK simplified-name compatibility is not full OpenCC-grade conversion; extra issuer-name pairs are added only when a live search misses.
- Some HK issuers only publish one language version PDF; `--lang` only changes selection priority.
- External site structure changes may require updates in the downloader modules.
- Chinese names still default to A-share. Use `--market hk` when the issuer may be listed in Hong Kong.

## Troubleshooting Map

- Name resolution problems: `scripts/report_downloader/stock_search.py`
- cninfo report matching problems: `scripts/report_downloader/downloader_cninfo.py`
- HKEX lookup or language-selection problems: `scripts/report_downloader/downloader_hkex.py`
- Download validation or network error problems: `scripts/report_downloader/utils.py`
- CLI invocation issues: `scripts/report_downloader/cli.py` or `scripts/run_report.py`
