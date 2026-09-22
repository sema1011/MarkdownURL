"""Тесты для модуля exceptions — кастомные исключения."""

from markdownurl.exceptions import (
    ExtractionError,
    FetchError,
    FetchTimeoutError,
    FileWriteError,
    ImageDownloadError,
    MarkdownURLError,
)


class TestMarkdownURLError:
    """Тесты базового исключения."""

    def test_inheritance(self) -> None:
        assert issubclass(MarkdownURLError, Exception)

    def test_message(self) -> None:
        exc = MarkdownURLError("Test message")
        assert str(exc) == "Test message"


class TestFetchError:
    """Тесты FetchError."""

    def test_inheritance(self) -> None:
        assert issubclass(FetchError, MarkdownURLError)

    def test_url_property(self) -> None:
        exc = FetchError("https://example.com", "Connection failed")
        assert exc.url == "https://example.com"

    def test_message(self) -> None:
        exc = FetchError("https://example.com", "Connection failed")
        assert "Connection failed" in str(exc)


class TestExtractionError:
    """Тесты ExtractionError."""

    def test_inheritance(self) -> None:
        assert issubclass(ExtractionError, MarkdownURLError)

    def test_url_property(self) -> None:
        exc = ExtractionError("https://example.com", "No content")
        assert exc.url == "https://example.com"


class TestFetchTimeoutError:
    """Тесты FetchTimeoutError."""

    def test_inheritance(self) -> None:
        assert issubclass(FetchTimeoutError, MarkdownURLError)

    def test_url_and_timeout(self) -> None:
        exc = FetchTimeoutError("https://example.com", 10.0)
        assert exc.url == "https://example.com"
        assert exc.timeout == 10.0


class TestFileWriteError:
    """Тесты FileWriteError."""

    def test_inheritance(self) -> None:
        assert issubclass(FileWriteError, MarkdownURLError)

    def test_path_property(self) -> None:
        from pathlib import Path
        exc = FileWriteError(Path("/tmp/test.md"), "Permission denied")
        assert exc.path == Path("/tmp/test.md")


class TestImageDownloadError:
    """Тесты ImageDownloadError."""

    def test_inheritance(self) -> None:
        assert issubclass(ImageDownloadError, MarkdownURLError)

    def test_url_and_message(self) -> None:
        exc = ImageDownloadError("https://example.com/img.jpg", "Network error")
        assert exc.url == "https://example.com/img.jpg"
        assert "Network error" in str(exc)
