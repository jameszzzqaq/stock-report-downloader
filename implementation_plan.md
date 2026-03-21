# 财报下载工具 (Financial Report Downloader)

Python 控制台工具，支持通过股票名称或代码、报告类型(年报/中报/季报)、年份自动下载 A股 和 港股 的财务报告 PDF。支持多语言版本选择，默认优先级：简体中文 > 繁体中文 > 英文。

## User Review Required

> [!IMPORTANT]
> **数据源选择**：A股使用巨潮资讯网 (cninfo.com.cn) 的公告查询接口；港股使用 HKEXnews 披露易的公告搜索页面。两者都不提供官方 API，实现基于网页请求模拟。
>
> **市场自动识别**：纯数字代码 6 位自动识别为 A股(上交所/深交所)；带 `.HK` 后缀或 5 位纯数字识别为港股。如有歧义需用户指定 `--market` 参数。

## Proposed Changes

### 项目结构

```
d:\project\invest\report_downloader\
├── __init__.py
├── __main__.py          # CLI 入口 (python -m report_downloader)
├── cli.py               # argparse 参数解析
├── downloader_cninfo.py # A股下载器 (巨潮资讯网)
├── downloader_hkex.py   # 港股下载器 (HKEXnews)
├── stock_search.py      # 股票名称/代码搜索辅助
├── utils.py             # 公共工具函数
└── requirements.txt     # Python 依赖
```

---

### CLI 入口

#### [NEW] [cli.py](file:///d:/project/invest/report_downloader/cli.py)

命令行参数解析，支持以下参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `stock` | 股票名称或代码 (位置参数) | `000001` / `平安银行` / `06049.HK` |
| `--type` / `-t` | 报告类型: `annual`(年报), `semi`(中报), `q1`(一季报), `q3`(三季报) | `-t annual` |
| `--year` / `-y` | 报告年份 | `-y 2024` |
| `--market` / `-m` | 强制指定市场: `a` / `hk` | `-m hk` |
| `--lang` / `-l` | 语言偏好: `sc`(简中), `tc`(繁中), `en`(英文) | `-l en` |
| `--output` / `-o` | 下载保存目录，默认当前目录 | `-o ./reports` |

使用示例：
```bash
python -m report_downloader 000001 -t annual -y 2024
python -m report_downloader 保利物业 -t semi -y 2024 -m hk
python -m report_downloader 06049 -t annual -y 2023 -l en
```

#### [NEW] [__main__.py](file:///d:/project/invest/report_downloader/__main__.py)

模块入口，调用 `cli.main()`。

---

### A股下载器 (巨潮资讯网)

#### [NEW] [downloader_cninfo.py](file:///d:/project/invest/report_downloader/downloader_cninfo.py)

- **API 端点**: `http://www.cninfo.com.cn/new/hisAnnouncement/query`
- **请求方式**: POST (form-data)
- **核心参数**:
  - `stock`: 股票代码 (如 `000001`)
  - `category`: 报告类型映射
    - 年报 → `category_ndbg_szsh`
    - 中报 → `category_bndbg_szsh`
    - 一季报 → `category_yjdbg_szsh`
    - 三季报 → `category_sjdbg_szsh`
  - `seDate`: 日期范围过滤 (用年份构造范围)
  - `column`: `szse`(深交所) 或 `sse`(上交所)
- **返回格式**: JSON，包含 `announcements` 列表，每项含 `adjunctUrl`(PDF路径)、`announcementTitle`(标题)
- **PDF 基础 URL**: `http://static.cninfo.com.cn/`
- **关键逻辑**:
  1. 根据股票代码前缀判断交易所 (6开头→上交所，其他→深交所)
  2. 发送 POST 获取公告列表
  3. 通过标题关键词过滤正确的报告 (排除摘要、修订稿等)
  4. 下载 PDF 到指定目录

---

### 港股下载器 (HKEXnews)

#### [NEW] [downloader_hkex.py](file:///d:/project/invest/report_downloader/downloader_hkex.py)

- **搜索页**: `https://www1.hkexnews.hk/search/titlesearch.xhtml`
  - 这是新版 HKEXnews 的搜索接口，返回 JSON 结果
- **请求方式**: GET 搜索请求
- **核心参数**:
  - `stock_id`: 股票代码 (如 `06049`)
  - `category`: 文件类型 (年报/中期报告等)
  - `from_date` / `to_date`: 日期范围
- **多语言支持**: 港股财报通常有中文/英文两个版本（有些公司为中英双语单一文件），通过标题关键词区分
- **关键逻辑**:
  1. 构建搜索请求，指定股票代码和文件类型
  2. 解析返回结果获取 PDF 下载链接
  3. 按语言偏好排序，优先下载用户偏好的语言版本
  4. 下载 PDF 到指定目录

---

### 股票搜索

#### [NEW] [stock_search.py](file:///d:/project/invest/report_downloader/stock_search.py)

- 当用户输入股票名称（非纯数字）时，使用搜索接口将名称转换为股票代码
- A股: 通过 cninfo 搜索接口查询
- 港股: 通过 hkexnews 或 yahoo finance 搜索
- 市场自动识别逻辑:
  - 包含 `.HK` 后缀 → 港股
  - 6位数字 + `6/9`开头 → 上交所
  - 6位数字 + 其他 → 深交所
  - 5位数字或更少 → 港股
  - 中文名称 → 先搜 A股，无结果再搜港股(或由 `--market` 指定)

---

### 公共工具

#### [NEW] [utils.py](file:///d:/project/invest/report_downloader/utils.py)

- HTTP 请求封装 (统一 headers、重试、超时)
- 文件名清理和格式化
- 下载进度显示
- 日志输出

#### [NEW] [requirements.txt](file:///d:/project/invest/report_downloader/requirements.txt)

```
requests>=2.28.0
beautifulsoup4>=4.11.0
```

## Verification Plan

### 手动测试

以下测试场景需要在有网络连接的环境下进行：

1. **A股年报下载** - 运行 `python -m report_downloader 000001 -t annual -y 2024 -o ./test_output`，验证成功下载平安银行2024年报 PDF
2. **港股年报下载** - 运行 `python -m report_downloader 06049 -t annual -y 2023 -m hk -o ./test_output`，验证成功下载保利物业2023年报 PDF
3. **股票名称搜索** - 运行 `python -m report_downloader 平安银行 -t annual -y 2024 -o ./test_output`，验证能通过名称找到对应代码并下载
4. **多语言测试** - 运行 `python -m report_downloader 06049 -t annual -y 2023 -m hk -l en -o ./test_output`，验证优先下载英文版本
5. **错误处理** - 运行 `python -m report_downloader 999999 -t annual -y 2024`，验证友好的错误提示
