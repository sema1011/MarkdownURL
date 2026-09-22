"""Тесты для модуля fetcher — HTTP-клиент."""

from markdownurl.exceptions import FetchError
from markdownurl.fetcher import Fetcher


class TestFetcher:
    """Тесты класса Fetcher."""

    def setup_method(self) -> None:
        self.fetcher = Fetcher(timeout=5.0)

    def test_detect_encoding_utf8(self) -> None:
        import httpx
        response = httpx.Response(200, headers={"Content-Type": "text/html; charset=utf-8"})
        encoding = self.fetcher.detect_encoding("<html></html>", response)
        assert encoding == "utf-8"

    def test_detect_encoding_from_meta(self) -> None:
        html = '<html><head><meta charset="windows-1251"></head><body></body></html>'
        import httpx
        response = httpx.Response(200)
        encoding = self.fetcher.detect_encoding(html, response)
        assert encoding == "windows-1251"

    def test_detect_encoding_fallback_utf8(self) -> None:
        html = "<html><body></body></html>"
        import httpx
        response = httpx.Response(200)
        encoding = self.fetcher.detect_encoding(html, response)
        assert encoding == "utf-8"

    def test_fetcher_max_retries(self) -> None:
        """Тест максимального количества попыток."""
        fetcher = Fetcher(timeout=1.0, max_retries=0)
        try:
            fetcher.fetch_and_decode("https://nonexistent.invalid.domain.test")
            raise AssertionError("Expected exception")
        except FetchError:
            pass  # Expected


class TestFetcherEncoding:
    """Тесты определения кодировки."""

    def setup_method(self) -> None:
        self.fetcher = Fetcher()

    def test_content_type_header_encoding(self) -> None:
        import httpx
        response = httpx.Response(200, headers={"Content-Type": "text/html; charset=iso-8859-1"})
        encoding = self.fetcher.detect_encoding("<html></html>", response)
        assert encoding == "iso-8859-1"

    def test_meta_http_equiv_encoding(self) -> None:
        html = '<html><head><meta http-equiv="Content-Type" content="text/html; charset=windows-1251"></head></html>'
        import httpx
        response = httpx.Response(200)
        encoding = self.fetcher.detect_encoding(html, response)
        assert encoding == "windows-1251"
