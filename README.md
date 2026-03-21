# 财报下载工具

一个基于 Python 的命令行工具，用于下载 A 股和港股上市公司的财务报告 PDF。

当前已支持：
- A 股年报、中报、一季报、三季报下载
- 港股年报、中报下载主流程
- 通过股票代码或股票名称搜索下载
- 港股按语言偏好优先下载中文或英文版本
- 输出文件名自动包含股票代码和股票名称

## 功能特性

- A 股数据源：`cninfo` 公告查询接口
- 港股数据源：`HKEXnews` 搜索与结果接口
- 自动市场识别：
  - 6 位纯数字默认识别为 A 股
  - 5 位数字或 `.HK` 后缀默认识别为港股
  - 中文名称默认优先按 A 股处理；如需港股请显式加 `--market hk`
- 股票名称搜索：
  - A 股名称搜索走 `cninfo` 实际可用的 `POST` 搜索接口
  - 港股名称搜索走 `HKEX partial.do`
  - 已补充港股简体名称兼容，例如 `保利物业` 可自动回退到繁体候选再搜索
- 年报披露窗口处理：
  - A 股和港股年报都会覆盖到次年披露期
- 文件名规则：
  - `股票代码_股票名称_年份_报告类型_报告标题.pdf`

## 环境要求

- Python 3.10+
- 可访问外部站点：`cninfo.com.cn`、`hkexnews.hk`

## 安装

```bash
uv sync
```

首次进入项目后，`uv` 会在本地创建虚拟环境并按 `uv.lock` 安装依赖。

如果你修改了依赖并希望更新锁文件：

```bash
uv lock
uv sync
```

如果需要新增依赖，推荐使用：

```bash
uv add requests beautifulsoup4
```

如果只想直接运行命令，不手动激活环境：

```bash
uv run stock-report-downloader --help
```

或者：

```bash
uv run python -m report_downloader --help
```

## 用法

```bash
uv run stock-report-downloader STOCK --type TYPE --year YEAR [options]
```

参数说明：

| 参数 | 说明 |
|---|---|
| `stock` | 股票代码或股票名称，例如 `000001`、`平安银行`、`06049`、`保利物业` |
| `--type`, `-t` | 报告类型：`annual`、`semi`、`q1`、`q3` |
| `--year`, `-y` | 报告年份 |
| `--market`, `-m` | 强制指定市场：`a` 或 `hk` |
| `--lang`, `-l` | 语言偏好：`sc`、`tc`、`en`，主要对港股生效 |
| `--output`, `-o` | 输出目录，默认当前目录 |

查看帮助：

```bash
uv run stock-report-downloader --help
```

或者：

```bash
uv run python -m report_downloader --help
```

## 使用示例

A 股代码下载：

```bash
uv run stock-report-downloader 000001 -t annual -y 2024 -o ./test_output
```

A 股名称下载：

```bash
uv run stock-report-downloader 平安银行 -t annual -y 2024 -o ./test_output
```

港股代码下载：

```bash
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -o ./test_output
```

港股名称下载：

```bash
uv run stock-report-downloader 保利物业 -t annual -y 2023 -m hk -o ./test_output
```

港股英文版优先：

```bash
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -l en -o ./test_output
```

## 当前项目结构

```text
stock-report-downloader/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── usage.md
├── scripts/
│   ├── run_report.py
│   ├── verify_examples.py
│   └── report_downloader/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── downloader_cninfo.py
│       ├── downloader_hkex.py
│       ├── stock_search.py
│       └── utils.py
├── .python-version
├── pyproject.toml
├── uv.lock
└── test_output/
```

## 已验证场景

以下命令已在当前环境实际跑通：

1. A 股代码下载
```bash
uv run stock-report-downloader 000001 -t annual -y 2024 -o ./test_output
```
输出示例：
`000001_平安银行_2024_annual_2024年年度报告.pdf`

2. 港股代码下载
```bash
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -o ./test_output
```
输出示例：
`06049_保利物業_2023_annual_2023年度報告.pdf`

3. A 股名称搜索下载
```bash
uv run stock-report-downloader 平安银行 -t annual -y 2024 -o ./test_output
```

4. 港股名称搜索下载
```bash
uv run stock-report-downloader 保利物业 -t annual -y 2023 -m hk -o ./test_output
```

5. 港股英文版优先下载
```bash
uv run stock-report-downloader 06049 -t annual -y 2023 -m hk -l en -o ./test_output
```
输出示例：
`06049_保利物業_2023_annual_2023 ANNUAL REPORT.pdf`

6. 错误处理
```bash
uv run stock-report-downloader 999999 -t annual -y 2024
```
返回非零退出码，并输出友好错误信息。

## 实现说明

### A 股

A 股下载逻辑位于 `scripts/report_downloader/downloader_cninfo.py`：
- 自动推导交易所与 `orgId`
- 用 `stock=代码,orgId` 访问 `cninfo` 公告接口
- 年报查询窗口扩展到次年，避免漏掉实际披露日期落在下一年的情况
- 通过公告标题过滤摘要、修订稿等非目标文档

### 港股

港股下载逻辑位于 `scripts/report_downloader/downloader_hkex.py`：
- 先通过 `partial.do` 解析 HKEX 内部 `stockId`
- 再通过 `titleSearchServlet.do` 获取结果列表
- 按标题、分类和语言偏好选择目标 PDF
- 年报查询窗口同样覆盖到次年披露期

### 名称搜索

名称搜索逻辑位于 `scripts/report_downloader/stock_search.py`：
- A 股名称搜索使用 `cninfo` 的 `POST /new/information/topSearch/query`
- 港股名称搜索使用 `HKEX partial.do`
- 对港股简体中文名增加了本地简转繁候选回退

## 已知限制

- 港股简体名兼容当前是轻量本地映射，不是完整的通用简繁转换库；常见公司名已可工作，但不能保证覆盖所有字符。
- HKEX 某些公司可能只提供单一语言版本 PDF，此时 `--lang` 只能影响选择顺序，不能生成不存在的语言版本。
- 目前没有自动化测试文件，验证主要通过真实联网命令完成。
- 程序依赖外部站点接口，若对方页面或参数结构变化，可能需要调整解析逻辑。

## 后续可优化项

- 引入更完整的简繁转换方案，提升港股简体名称搜索覆盖率
- 增加自动化测试和接口回归测试
- 补充 `README` 中的更多案例与常见错误说明
- 为输出文件增加可选的日期或语言后缀
