from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from report_downloader.downloader_hkex import _detect_language_from_link, _resolve_stock_id
from report_downloader.stock_search import _search_hk_by_single_name
from report_downloader.utils import DownloadError, StockTarget, download_file


class DownloadFileTests(unittest.TestCase):
    def test_rejects_html_content_type(self) -> None:
        session = Mock()
        response = Mock()
        response.headers = {"Content-Type": "text/html; charset=utf-8"}
        session.request.return_value = response
        response.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "report.pdf"
            with self.assertRaises(DownloadError):
                download_file(session, "https://www1.hkexnews.hk/report.pdf", destination)
            self.assertFalse(destination.exists())

    def test_rejects_non_pdf_payload(self) -> None:
        session = Mock()
        response = Mock()
        response.headers = {"Content-Type": "application/octet-stream"}
        response.iter_content.return_value = iter([b"<html>not a pdf</html>"])
        session.request.return_value = response
        response.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "report.pdf"
            with self.assertRaises(DownloadError):
                download_file(session, "https://www1.hkexnews.hk/report.pdf", destination)
            self.assertFalse(destination.exists())

    def test_accepts_pdf_payload(self) -> None:
        session = Mock()
        response = Mock()
        response.headers = {"Content-Type": "application/pdf", "Content-Length": "21"}
        response.iter_content.return_value = iter([b"%PDF-1.4\nbody", b"\n%%EOF"])
        session.request.return_value = response
        response.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "report.pdf"
            result = download_file(session, "https://www1.hkexnews.hk/report.pdf", destination)
            self.assertEqual(result, destination)
            self.assertTrue(destination.exists())


class HkexSearchTests(unittest.TestCase):
    def test_search_raises_on_malformed_callback_json(self) -> None:
        session = Mock()
        response = Mock()
        response.text = "callback({bad json});"
        session.request.return_value = response
        response.raise_for_status.return_value = None

        with self.assertRaisesRegex(Exception, "无法解析"):
            _search_hk_by_single_name("保利物业", session)

    def test_search_does_not_fallback_to_first_non_matching_result(self) -> None:
        session = Mock()
        response = Mock()
        response.text = 'callback({"stockInfo":[{"name":"错误公司","code":"12345","stockId":"999999999"}]});'
        session.request.return_value = response
        response.raise_for_status.return_value = None

        result = _search_hk_by_single_name("保利物业", session)
        self.assertIsNone(result)

    def test_resolve_stock_id_does_not_fallback_to_first_non_matching_result(self) -> None:
        session = Mock()
        response = Mock()
        response.text = 'callback({"stockInfo":[{"name":"错误公司","code":"12345","stockId":"999999999"}]});'
        session.request.return_value = response
        response.raise_for_status.return_value = None
        stock = StockTarget(query="06049", code="06049", market="hk")

        with self.assertRaisesRegex(Exception, "未找到港股代码"):
            _resolve_stock_id(stock, session)

    def test_detect_language_from_link_is_stable(self) -> None:
        self.assertEqual(_detect_language_from_link("/path/report_c.pdf"), "zh")
        self.assertEqual(_detect_language_from_link("/path/report_e.pdf"), "en")
        self.assertEqual(_detect_language_from_link("/path/report_ce.pdf"), "bilingual")
        self.assertEqual(_detect_language_from_link("/path/report.pdf"), "unknown")


if __name__ == "__main__":
    unittest.main()
