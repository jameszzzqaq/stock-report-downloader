from __future__ import annotations

import json
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
    download_file,
    ensure_directory,
    request,
)


HKEX_SEARCH_URL = "https://www1.hkexnews.hk/search/titlesearch.xhtml"
HKEX_SERVLET_URL = "https://www1.hkexnews.hk/search/titleSearchServlet.do"
HKEX_PARTIAL_URL = "https://www1.hkexnews.hk/search/partial.do"
HKEX_BASE_URL = "https://www1.hkexnews.hk/"
HKEX_ALLOWED_HOSTS = {"www1.hkexnews.hk"}
HKEX_LOOKUP_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": HKEX_SEARCH_URL,
}
HKEX_KEYWORDS = {
    "annual": ("annual report", "年度報告", "年度报告", "年報", "年报"),
    "semi": ("interim report", "中期報告", "中期报告", "half-year report", "half year report"),
    "q1": ("first quarterly", "1st quarterly", "第一季度", "一季度", "首季度"),
    "q3": ("third quarterly", "3rd quarterly", "第三季度", "三季度"),
}
HKEX_LONG_TEXT_KEYWORDS = {
    "annual": ("[年報]", "[年报]", "annual report"),
    "semi": ("[中期/半年度報告]", "[中期/半年度报告]", "interim report"),
    "q1": ("[第一季度", "first quarterly"),
    "q3": ("[第三季度", "third quarterly"),
}
HKEX_EXCLUDE = {
    "annual": ("業績公告", "业绩公告", "results announcement", "補充公告", "补充公告"),
    "semi": ("業績公告", "业绩公告", "results announcement"),
    "q1": (),
    "q3": (),
}
LANGUAGE_PREFERENCE = {
    "sc": {"zh": 0, "tc": 0, "bilingual": 1, "en": 2, "unknown": 3},
    "tc": {"tc": 0, "zh": 0, "bilingual": 1, "en": 2, "unknown": 3},
    "en": {"en": 0, "bilingual": 1, "zh": 2, "tc": 2, "unknown": 3},
}


def download_hkex_report(
    stock: StockTarget,
    report_type: str,
    year: int,
    output_dir: str | Path,
    *,
    language: str = "sc",
    session: requests.Session | None = None,
) -> Path:
    active_session = session or build_session()
    document = find_hkex_report(stock, report_type, year, language=language, session=active_session)
    directory = ensure_directory(output_dir)
    filename = document.filename_hint or build_output_filename(stock, year, report_type, document.title)
    destination = directory / filename
    return download_file(active_session, document.url, destination, allowed_hosts=HKEX_ALLOWED_HOSTS)


def find_hkex_report(
    stock: StockTarget,
    report_type: str,
    year: int,
    *,
    language: str = "sc",
    session: requests.Session | None = None,
) -> ReportDocument:
    active_session = session or build_session()
    stock_id = _resolve_stock_id(stock, active_session)
    payload = _query_hkex(stock_id, report_type, year, language, active_session)
    documents = _extract_documents(payload, stock, report_type, year, language)
    if not documents:
        params = _build_servlet_params(stock_id, report_type, year, language)
        debug_query = "&".join(f"{key}={value}" for key, value in params.items())
        raise ReportNotFoundError(f"未找到港股报告，查询地址: {HKEX_SERVLET_URL}?{debug_query}")
    chosen = documents[0]
    chosen.filename_hint = build_output_filename(stock, year, report_type, chosen.title)
    return chosen


def _resolve_stock_id(stock: StockTarget, session: requests.Session) -> str:
    if stock.stock_id and stock.stock_id.isdigit() and len(stock.stock_id) > 8:
        return stock.stock_id

    response = request(
        session,
        "GET",
        HKEX_PARTIAL_URL,
        params={
            "lang": "ZH",
            "type": "A",
            "name": stock.code,
            "market": "SEHK",
            "callback": "callback",
        },
        headers=HKEX_LOOKUP_HEADERS,
    )
    matches = re.search(r"callback\((.*)\)\s*;?\s*$", response.text, re.S)
    if not matches:
        raise ReportNotFoundError(f"无法解析港股代码 {stock.code} 的 HKEX 证券标识。")
    try:
        payload = json.loads(matches.group(1))
    except json.JSONDecodeError as exc:
        raise ReportNotFoundError(f"无法解析港股代码 {stock.code} 的 HKEX 证券标识。") from exc
    stock_info = payload.get("stockInfo", [])
    for item in stock_info:
        if str(item.get("code", "")).zfill(5) == stock.code:
            stock.name = stock.name or str(item.get("name", "")).strip()
            stock.stock_id = str(item.get("stockId", "")).strip()
            return stock.stock_id
    raise ReportNotFoundError(f"未找到港股代码 {stock.code} 对应的 HKEX 证券标识。")


def _query_hkex(
    stock_id: str,
    report_type: str,
    year: int,
    language: str,
    session: requests.Session,
) -> dict:
    response = request(
        session,
        "GET",
        HKEX_SERVLET_URL,
        params=_build_servlet_params(stock_id, report_type, year, language),
        headers=HKEX_LOOKUP_HEADERS,
    )
    try:
        return response.json()
    except ValueError as exc:
        raise ReportNotFoundError("HKEX 返回了无法解析的搜索结果。") from exc


def _build_servlet_params(stock_id: str, report_type: str, year: int, language: str) -> dict[str, str]:
    query_language = "E" if language == "en" else "zh"
    start_year, end_year = _filing_year_window(report_type, year)
    return {
        "sortDir": "0",
        "sortByOptions": "DateTime",
        "category": "0",
        "market": "SEHK",
        "stockId": stock_id,
        "documentType": "",
        "fromDate": f"{start_year}0101",
        "toDate": f"{end_year}1231",
        "title": "",
        "searchType": "1",
        "t1code": "",
        "t2Gcode": "",
        "t2code": "",
        "rowRange": "200",
        "lang": query_language,
    }


def _filing_year_window(report_type: str, year: int) -> tuple[int, int]:
    if report_type == "annual":
        return year, year + 1
    return year, year


def _extract_documents(
    payload: dict,
    stock: StockTarget,
    report_type: str,
    year: int,
    preferred_language: str,
) -> list[ReportDocument]:
    raw_result = payload.get("result", "[]")
    try:
        items = json.loads(raw_result)
    except (TypeError, json.JSONDecodeError):
        items = []

    documents: list[ReportDocument] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        stock_name = str(item.get("STOCK_NAME") or "").strip()
        if stock_name and not stock.name:
            stock.name = stock_name
        title = str(item.get("TITLE") or "").strip()
        long_text = str(item.get("LONG_TEXT") or "").strip()
        file_link = str(item.get("FILE_LINK") or "").strip()
        published_at = str(item.get("DATE_TIME") or "").strip()
        if not title or not file_link:
            continue
        if not _matches_report(title, long_text, report_type, year):
            continue
        documents.append(
            ReportDocument(
                title=title,
                url=absolute_url(HKEX_BASE_URL, file_link, allowed_hosts=HKEX_ALLOWED_HOSTS),
                language=_detect_language_from_link(file_link),
                published_at=published_at,
            )
        )

    documents.sort(key=lambda item: (_language_rank(item.language, preferred_language), _published_sort_key(item.published_at)))
    return documents


def _matches_report(title: str, long_text: str, report_type: str, year: int) -> bool:
    normalized = title.lower()
    normalized_long = long_text.lower()
    compact = re.sub(r"\s+", "", title)
    if str(year) not in compact:
        return False
    if any(keyword.lower() in normalized for keyword in HKEX_EXCLUDE[report_type]):
        return False
    if any(keyword.lower() in normalized for keyword in HKEX_KEYWORDS[report_type]):
        return True
    return any(keyword.lower() in normalized_long for keyword in HKEX_LONG_TEXT_KEYWORDS[report_type])


def _detect_language_from_link(file_link: str) -> str:
    lowered = file_link.lower()
    if lowered.endswith(("_ce.pdf", "_ec.pdf")):
        return "bilingual"
    if lowered.endswith("_c.pdf"):
        return "zh"
    if lowered.endswith("_e.pdf"):
        return "en"
    if lowered.endswith(".pdf"):
        return "unknown"
    return "unknown"


def _language_rank(language: str, preferred: str) -> int:
    return LANGUAGE_PREFERENCE.get(preferred, LANGUAGE_PREFERENCE['sc']).get(language, 99)


def _published_sort_key(value: str) -> tuple[int, int, int, str]:
    match = re.match(r'(\d{2})/(\d{2})/(\d{4})', value)
    if not match:
        return (0, 0, 0, value)
    day, month, year = match.groups()
    return (-int(year), -int(month), -int(day), value)
