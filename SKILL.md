---
name: stock-report-downloader
description: Download A-share and Hong Kong stock financial report PDFs (annual, semi, q1, q3) from cninfo and HKEX by stock code or company name. Use when a user asks to download 年报, 中报, 季报, 财报, A-share or HK reports, HKEX filings, 巨潮资讯 PDFs, or to run stock-report-downloader. Prefer this bundled CLI instead of writing scrape scripts.
compatibility: Requires Python 3.10+, uv (or pip + requests), and HTTPS access to www.cninfo.com.cn and www1.hkexnews.hk
metadata:
  version: "0.1.0"
---

# Stock Report Downloader

Download A-share and HK financial report PDFs with the bundled CLI. Do not scrape cninfo or HKEX yourself.

This directory is a portable [Agent Skill](https://agentskills.io). Install it as `stock-report-downloader` under `.agents/skills/` (project) or `~/.agents/skills/` (user). Codex can also use this repository as the skill root.

## Inputs

Collect these before running:

- `stock`: code or company name (`000001`, `平安银行`, `06049`, `06049.HK`)
- `--type`: `annual` | `semi` | `q1` | `q3`
- `--year`: report year
- `--output`: always set this to the user's requested folder, or the user's current working directory

Optional:

- `--market hk` when a Chinese name might be a Hong Kong issuer. Numeric codes are inferred (`6` digits → A-share, `≤5` digits or `.HK` → HK). Chinese names default to A-share.
- `--lang sc|tc|en` only changes HK language priority. Some issuers publish one language.

If a required input is missing, ask. Do not guess `--market` for an ambiguous Chinese name.

## Workflow

1. Resolve the skill root (the directory that contains this `SKILL.md`).
2. Run the bundled script from that root. Always pass `--output` so files do not land inside the skill folder.

```bash
uv run scripts/run_report.py STOCK --type TYPE --year YEAR --output OUTPUT_DIR
```

If `uv` is unavailable:

```bash
python3 -m pip install -q "requests>=2.28.0"
python3 scripts/run_report.py STOCK --type TYPE --year YEAR --output OUTPUT_DIR
```

3. Report the saved PDF path from the CLI (`下载完成: ...`). On failure, show the error and stop; do not hand-roll a downloader.

## Examples

```bash
uv run scripts/run_report.py 000001 -t annual -y 2024 -o "$OUTPUT_DIR"
uv run scripts/run_report.py 平安银行 -t annual -y 2024 -o "$OUTPUT_DIR"
uv run scripts/run_report.py 06049 -t annual -y 2023 -m hk -o "$OUTPUT_DIR"
uv run scripts/run_report.py 保利物业 -t annual -y 2023 -m hk -o "$OUTPUT_DIR"
uv run scripts/run_report.py 06049 -t annual -y 2023 -m hk -l en -o "$OUTPUT_DIR"
```

## Gotchas

- Always pass `--output`. The CLI default is `.`, which writes into the skill directory if you `cd` here.
- Chinese names without `--market` are treated as A-share. Use `--market hk` for Hong Kong names.
- `--lang` does not create a missing language version.
- Annual reports may be filed in the next calendar year; the CLI already searches that window.
- Output names look like `{code}_{name}_{year}_{type}_{title}.pdf`. Keep that convention unless the user asks otherwise.

## When something fails

Read [references/usage.md](references/usage.md) for verified commands and the troubleshooting map.

- Name or code resolution: `scripts/report_downloader/stock_search.py`
- A-share / cninfo match: `scripts/report_downloader/downloader_cninfo.py`
- HKEX lookup or language: `scripts/report_downloader/downloader_hkex.py`
- PDF / network validation: `scripts/report_downloader/utils.py`
- CLI flags: `scripts/report_downloader/cli.py`

Offline checks (from the skill root):

```bash
uv run python -m unittest discover -s tests -v
uv run scripts/verify_examples.py --list --details
```

## Patching this skill

Only when the user is fixing this downloader: edit the modules above, keep the `uv` + `scripts/run_report.py` entrypoint, and update `references/usage.md` together with any changed example.
