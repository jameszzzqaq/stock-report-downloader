from __future__ import annotations

import argparse
from pathlib import Path

from .downloader_cninfo import download_cninfo_report
from .downloader_hkex import download_hkex_report
from .stock_search import resolve_stock
from .utils import DownloaderError, build_session, configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="下载 A 股或港股财报 PDF。")
    parser.add_argument("stock", help="股票名称或代码，例如 000001、平安银行、06049.HK")
    parser.add_argument(
        "--type",
        "-t",
        choices=("annual", "semi", "q1", "q3"),
        required=True,
        dest="report_type",
        help="报告类型",
    )
    parser.add_argument("--year", "-y", type=int, required=True, help="报告年份")
    parser.add_argument("--market", "-m", choices=("a", "hk"), help="强制指定市场")
    parser.add_argument(
        "--lang",
        "-l",
        choices=("sc", "tc", "en"),
        default="sc",
        help="语言偏好，港股报告优先按此排序",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=".",
        help="输出目录，默认当前目录",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logger = configure_logging()
    session = build_session()

    try:
        stock = resolve_stock(args.stock, args.market, session=session)
        logger.info("已识别股票: %s %s (%s)", stock.code, stock.name or stock.query, stock.market)
        if stock.market == "a":
            destination = download_cninfo_report(
                stock,
                args.report_type,
                args.year,
                Path(args.output),
                session=session,
            )
        else:
            destination = download_hkex_report(
                stock,
                args.report_type,
                args.year,
                Path(args.output),
                language=args.lang,
                session=session,
            )
        logger.info("下载完成: %s", destination)
        return 0
    except DownloaderError as exc:
        logger.error("错误: %s", exc)
        return 1
