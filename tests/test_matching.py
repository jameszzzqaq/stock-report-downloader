from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from report_downloader.cli import main
from report_downloader.downloader_cninfo import _extract_documents, _matches_title
from report_downloader.downloader_hkex import _matches_report
from report_downloader.stock_search import (
    SIMPLE_TO_TRADITIONAL_MAP,
    _hk_name_candidates,
    infer_market,
    resolve_stock,
    search_cninfo_by_name,
)
from report_downloader.utils import (
    DownloadError,
    SearchError,
    StockTarget,
    safe_json,
    validate_remote_url,
)


class InferMarketTests(unittest.TestCase):
    def test_numeric_and_suffix_rules(self) -> None:
        self.assertEqual(infer_market("000001"), "a")
        self.assertEqual(infer_market("06049"), "hk")
        self.assertEqual(infer_market("6049.HK"), "hk")
        self.assertEqual(infer_market("平安银行"), "a")
        self.assertEqual(infer_market("保利物业", "hk"), "hk")

    def test_requires_market_for_english_name(self) -> None:
        with self.assertRaises(SearchError):
            infer_market("Ping An")


class NameResolutionTests(unittest.TestCase):
    def test_numeric_codes_do_not_hit_the_network(self) -> None:
        a_stock = resolve_stock("000001")
        self.assertEqual((a_stock.code, a_stock.market, a_stock.exchange), ("000001", "a", "szse"))
        hk_stock = resolve_stock("06049", "hk")
        self.assertEqual((hk_stock.code, hk_stock.market), ("06049", "hk"))

    def test_cninfo_does_not_fallback_to_first_unrelated_result(self) -> None:
        session = Mock()
        response = Mock()
        response.json.return_value = [{"zwjc": "错误公司", "code": "999999"}]
        session.request.return_value = response
        response.raise_for_status.return_value = None

        self.assertIsNone(search_cninfo_by_name("平安银行", session))

    def test_cninfo_prefers_exact_name_over_substring(self) -> None:
        session = Mock()
        response = Mock()
        response.json.return_value = [
            {"zwjc": "平安银行科技", "code": "300001"},
            {"zwjc": "平安银行", "code": "000001"},
        ]
        session.request.return_value = response
        response.raise_for_status.return_value = None

        result = search_cninfo_by_name("平安银行", session)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "000001")

    def test_hk_simplified_name_adds_traditional_candidate(self) -> None:
        self.assertIn("保利物業", _hk_name_candidates("保利物业"))
        self.assertIn("中國平安集團", _hk_name_candidates("中国平安集团"))
        self.assertEqual(SIMPLE_TO_TRADITIONAL_MAP["团"], "團")


class TitleMatchingTests(unittest.TestCase):
    def test_cninfo_keeps_full_report_and_drops_summaries(self) -> None:
        self.assertTrue(_matches_title("2024年年度报告", "annual", 2024))
        self.assertFalse(_matches_title("2024年年度报告摘要", "annual", 2024))
        self.assertFalse(_matches_title("2023年年度报告", "annual", 2024))

    def test_cninfo_ranks_full_text_ahead_of_notice(self) -> None:
        stock = StockTarget(query="000001", code="000001", market="a")
        announcements = [
            {
                "secName": "平安银行",
                "announcementTitle": "2024年年度报告公告",
                "adjunctUrl": "finalpage/2024-01-01/notice.pdf",
            },
            {
                "secName": "平安银行",
                "announcementTitle": "2024年年度报告全文",
                "adjunctUrl": "finalpage/2024-01-01/full.pdf",
            },
        ]
        documents = _extract_documents(announcements, stock, "annual", 2024)
        self.assertEqual(documents[0].title, "2024年年度报告全文")

    def test_hkex_quarterly_keywords_do_not_cross_match(self) -> None:
        self.assertTrue(_matches_report("2024 First Quarterly Report", "", "q1", 2024))
        self.assertFalse(_matches_report("2024 Third Quarterly Report", "", "q1", 2024))
        self.assertTrue(_matches_report("2024 Third Quarterly Report", "", "q3", 2024))
        self.assertFalse(_matches_report("2024 First Quarterly Report", "", "q3", 2024))
        self.assertFalse(_matches_report("2024 Quarterly Report", "quarterly report", "q1", 2024))


class UtilityTests(unittest.TestCase):
    def test_safe_json_returns_empty_on_invalid_payload(self) -> None:
        response = Mock()
        response.json.side_effect = ValueError("bad json")
        self.assertEqual(safe_json(response), {})

    def test_rejects_http_download_url(self) -> None:
        with self.assertRaises(DownloadError):
            validate_remote_url("http://www.cninfo.com.cn/report.pdf")


class CliTests(unittest.TestCase):
    def test_missing_report_exits_nonzero(self) -> None:
        with patch("report_downloader.cli.resolve_stock", side_effect=SearchError("未找到股票")):
            self.assertEqual(main(["999999", "-t", "annual", "-y", "2024"]), 1)

    def test_successful_a_share_download_returns_zero(self) -> None:
        stock = StockTarget(query="000001", code="000001", market="a", name="平安银行")
        with (
            patch("report_downloader.cli.resolve_stock", return_value=stock),
            patch("report_downloader.cli.download_cninfo_report", return_value=Path("out.pdf")),
        ):
            self.assertEqual(main(["000001", "-t", "annual", "-y", "2024", "-o", "./tmp"]), 0)


if __name__ == "__main__":
    unittest.main()
