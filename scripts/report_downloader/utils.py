from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests


DEFAULT_TIMEOUT = 20
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
SECURE_SCHEMES = {"https"}


class DownloaderError(Exception):
    """Base error for the downloader package."""


class SearchError(DownloaderError):
    """Raised when a stock search cannot be resolved."""


class ReportNotFoundError(DownloaderError):
    """Raised when a report cannot be found."""


class DownloadError(DownloaderError):
    """Raised when downloading a file fails."""


@dataclass(slots=True)
class StockTarget:
    query: str
    code: str
    market: str
    name: str = ""
    exchange: str = ""
    org_id: str = ""
    stock_id: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReportDocument:
    title: str
    url: str
    language: str = "unknown"
    published_at: str = ""
    filename_hint: str = ""


def configure_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return logging.getLogger("report_downloader")


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def request(
    session: requests.Session,
    method: str,
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 3,
    retry_delay: float = 1.0,
    **kwargs: Any,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = session.request(method=method, url=url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(retry_delay * attempt)
    raise DownloadError(f"请求失败: {url}") from last_error


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def sanitize_filename(value: str, max_length: int = 150) -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value).strip()
    value = re.sub(r"\s+", " ", value)
    if not value:
        value = "report"
    return value[:max_length].rstrip(". ")


def year_date_range(year: int) -> str:
    return f"{year}-01-01~{year}-12-31"


def report_publish_date_range(report_type: str, year: int) -> str:
    if report_type == "annual":
        return f"{year}-01-01~{year + 1}-12-31"
    return year_date_range(year)


def normalize_hk_code(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    return digits.zfill(5)


def normalize_a_code(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    return digits.zfill(6)


def derive_cninfo_org_id(code: str, exchange: str) -> str:
    prefix = "gssh" if exchange == "sse" else "gssz"
    return f"{prefix}0{code}"


def is_chinese_text(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def download_file(
    session: requests.Session,
    url: str,
    destination: Path,
    *,
    chunk_size: int = 65536,
    allowed_hosts: set[str] | None = None,
) -> Path:
    validate_remote_url(url, allowed_hosts=allowed_hosts)
    response = request(session, "GET", url, stream=True)
    _validate_download_response(response, url)
    total = int(response.headers.get("Content-Length", 0))
    received = 0
    first_chunk = True
    try:
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                if first_chunk:
                    _validate_pdf_signature(chunk, url)
                    first_chunk = False
                handle.write(chunk)
                received += len(chunk)
                if total:
                    percent = received * 100 // total
                    print(f"\r下载中: {percent:3d}% ", end="", flush=True)
        if first_chunk:
            raise DownloadError(f"下载内容为空: {url}")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    if total:
        print("\r下载完成      ")
    return destination


def _validate_download_response(response: requests.Response, url: str) -> None:
    content_type = (response.headers.get("Content-Type") or "").lower()
    suspicious_markers = ("text/html", "text/plain", "application/json", "text/json", "xml")
    if any(marker in content_type for marker in suspicious_markers):
        raise DownloadError(f"下载地址未返回 PDF 内容: {url}")


def _validate_pdf_signature(chunk: bytes, url: str) -> None:
    if not chunk.lstrip().startswith(b"%PDF-"):
        raise DownloadError(f"下载地址未返回有效 PDF 文件: {url}")


def build_output_filename(
    stock: StockTarget,
    year: int,
    report_type: str,
    title: str,
) -> str:
    parts = [stock.code]
    preferred_name = (stock.name or "").strip()
    fallback_name = (stock.query or "").strip()
    if preferred_name and preferred_name != stock.code:
        parts.append(preferred_name)
    elif fallback_name and fallback_name != stock.code:
        parts.append(fallback_name)
    parts.extend([str(year), report_type, sanitize_filename(title)])
    return sanitize_filename("_".join(parts)) + ".pdf"


def absolute_url(
    base_url: str,
    maybe_relative: str,
    *,
    allowed_hosts: set[str] | None = None,
) -> str:
    combined = urljoin(base_url, maybe_relative)
    validate_remote_url(combined, allowed_hosts=allowed_hosts)
    return combined


def validate_remote_url(url: str, *, allowed_hosts: set[str] | None = None) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if scheme not in SECURE_SCHEMES:
        raise DownloadError(f"拒绝不安全的下载地址: {url}")
    if allowed_hosts and host not in {value.lower() for value in allowed_hosts}:
        raise DownloadError(f"拒绝非白名单下载地址: {url}")
    return url


def safe_json(response: requests.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return {}


def names_match(query: str, candidate: str) -> bool:
    return bool(query) and bool(candidate) and (query == candidate or query in candidate or candidate in query)
