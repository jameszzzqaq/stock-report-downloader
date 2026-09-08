# 财报下载工具

按股票代码或公司名，从[巨潮资讯](https://www.cninfo.com.cn/)和[港交所披露易](https://www1.hkexnews.hk/)下载 A 股 / 港股财务报告 PDF。

## 要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- 能访问 `cninfo.com.cn`、`hkexnews.hk`

```bash
uv sync
uv run stock-report-downloader --help
```

## 用法

```bash
uv run stock-report-downloader STOCK --type TYPE --year YEAR [options]
```

| 参数 | 说明 |
|---|---|
| `STOCK` | 代码或名称，如 `000001`、`平安银行`、`06049`、`保利物业` |
| `-t, --type` | `annual` / `semi` / `q1` / `q3` |
| `-y, --year` | 报告年份 |
| `-m, --market` | 强制市场：`a` 或 `hk` |
| `-l, --lang` | 港股语言偏好：`sc`（默认）、`tc`、`en` |
| `-o, --output` | 输出目录，默认当前目录 |

```bash
# A 股：代码或名称
uv run stock-report-downloader 000001 -t annual -y 2024 -o ./test_output
uv run stock-report-downloader 平安银行 -t annual -y 2024 -o ./test_output

# 港股：中文名可能被当成 A 股，请显式加 -m hk
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -o ./test_output
uv run stock-report-downloader 保利物业 -t annual -y 2023 -m hk -o ./test_output

# 港股优先英文版（只有一种语言时仍会下载现有版本）
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -l en -o ./test_output
```

已核对过的命令和预期结果见 [`references/usage.md`](references/usage.md)。

## 市场识别

未指定 `--market` 时：

- 6 位数字 → A 股
- 1–5 位数字或 `*.HK` → 港股
- 中文名称 → 默认按 A 股搜；港股请加 `-m hk`
- 英文名称无法自动判断，必须指定 `--market`

名称搜索先精确匹配再子串匹配，不会随便取第一条无关结果。港股简体名会先做一层本地简转繁再查。

## 输出

文件名：`代码_名称_年份_类型_标题.pdf`

年报会查到次年披露窗口，避免漏掉跨年发布的报告。下载只接受 HTTPS 且校验 PDF 魔数；HTML / 非 PDF 响应会失败并删掉半成品。

## 项目结构

```text
scripts/report_downloader/
  cli.py                 # 命令行入口
  stock_search.py        # 代码 / 名称解析
  downloader_cninfo.py   # A 股（巨潮）
  downloader_hkex.py     # 港股（披露易）
  utils.py               # 会话、校验、文件名
tests/                   # 离线单测
references/usage.md      # 已验证命令
SKILL.md                 # Codex / Cursor skill
```

```bash
uv run python -m unittest discover -s tests -v
uv run python scripts/verify_examples.py --list --details
```

`verify_examples.py` 会打真实站点，改下载逻辑后再按需跑。日常开发先跑离线测试。

## 限制

- 港股简转繁是本地对照表，不是完整 OpenCC。
- `--lang` 只改港股选择顺序，不会凭空造出不存在的语言版本。
- 外部站点改接口时，对应模块可能要跟着改。

本仓库同时是 Codex / Cursor skill：在仓库里下财报或修下载器时，优先走现有 CLI，不要另写爬虫。
