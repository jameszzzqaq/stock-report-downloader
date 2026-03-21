from __future__ import annotations

import re
from pathlib import Path

import requests

from .utils import (
    ReportDocument,
    ReportNotFoundError,
    StockTarget,
    absolute_url,
    build_output_filename,
    build_session,
    derive_cninfo_org_id,
    download_file,
    ensure_directory,
    report_publish_date_range,
    request,
)


CNINFO_QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_PDF_BASE_URL = "http://static.cninfo.com.cn/"
CNINFO_CATEGORY_MAP = {
    "annual": "category_ndbg_szsh",
    "semi": "category_bndbg_szsh",
    "q1": "category_yjdbg_szsh",
    "q3": "category_sjdbg_szsh",
}
CNINFO_TITLE_KEYWORDS = {
    "annual": ("年度报告", "年报", "Annual Report"),
    "semi": ("半年度报告", "中期报告", "中报", "Interim Report"),
    "q1": ("第一季度报告", "一季度报告", "First Quarterly"),
    "q3": ("第三季度报告", "三季度报告", "Third Quarterly"),
}
CNINFO_EXCLUDE_KEYWORDS = ("摘要", "英文版", "取消", "更正", "修订", "说明会", "问询函")
CNINFO_REQUEST_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "http://www.cninfo.com.cn",
    "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
}


def download_cninfo_report(
    stock: StockTarget,
    report_type: str,
    year: int,
    output_dir: str | Path,
    *,
    session: requests.Session | None = None,
) -> Path:
    active_session = session or build_session()
    document = find_cninfo_report(stock, report_type, year, session=active_session)
    directory = ensure_directory(output_dir)
    filename = document.filename_hint or build_output_filename(stock, year, report_type, document.title)
    destination = directory / filename
    return download_file(active_session, document.url, destination)


def find_cninfo_report(
    stock: StockTarget,
    report_type: str,
    year: int,
    *,
    session: requests.Session | None = None,
) -> ReportDocument:
    active_session = session or build_session()
    payload = _build_query_payload(stock, report_type, year)
    response = request(
        active_session,
        "POST",
        CNINFO_QUERY_URL,
        data=payload,
        headers=CNINFO_REQUEST_HEADERS,
    )
    data = _safe_json(response)
    announcements = data.get("announcements") if isinstance(data, dict) else []
    documents = _extract_documents(announcements or [], stock, report_type, year)
    if not documents:
        raise ReportNotFoundError(f"未找到 {stock.code} 的 {year} 年 {report_type} 报告。")
    return documents[0]


def _build_query_payload(stock: StockTarget, report_type: str, year: int) -> dict[str, str | int]:
    exchange = stock.exchange or ("sse" if stock.code.startswith(("6", "9")) else "szse")
    org_id = stock.org_id or derive_cninfo_org_id(stock.code, exchange)
    return {
        "pageNum": 1,
        "pageSize": 50,
        "column": exchange,
        "tabName": "fulltext",
        "plate": "",
        "stock": f"{stock.code},{org_id}",
        "searchkey": "",
        "secid": "",
        "category": CNINFO_CATEGORY_MAP[report_type],
        "trade": "",
        "seDate": report_publish_date_range(report_type, year),
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }


def _extract_documents(
    announcements: list[dict],
    stock: StockTarget,
    report_type: str,
    year: int,
) -> list[ReportDocument]:
    results: list[ReportDocument] = []
    for item in announcements:
        sec_name = str(item.get("secName") or item.get("secname") or "").strip()
        if sec_name and not stock.name:
            stock.name = sec_name
        title = str(item.get("announcementTitle") or "").strip()
        adjunct = str(item.get("adjunctUrl") or "").strip()
        published = str(item.get("announcementTime") or item.get("announcementDate") or "")
        if not title or not adjunct:
            continue
        if not _matches_title(title, report_type, year):
            continue
        results.append(
            ReportDocument(
                title=title,
                url=absolute_url(CNINFO_PDF_BASE_URL, adjunct),
                language="sc",
                published_at=published,
                filename_hint=build_output_filename(stock, year, report_type, title),
            )
        )
    results.sort(key=lambda document: _title_rank(document.title))
    return results


def _matches_title(title: str, report_type: str, year: int) -> bool:
    normalized_title = re.sub(r"\s+", "", title)
    if str(year) not in normalized_title:
        return False
    if any(keyword in normalized_title for keyword in CNINFO_EXCLUDE_KEYWORDS):
        return False
    return any(keyword.replace(" ", "") in normalized_title for keyword in CNINFO_TITLE_KEYWORDS[report_type])


def _title_rank(title: str) -> tuple[int, int]:
    penalty = 0
    if "公告" in title:
        penalty += 1
    if "全文" in title:
        penalty -= 1
    return (penalty, len(title))


def _safe_json(response: requests.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return {}

