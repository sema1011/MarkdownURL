"""Тесты для fetch_article, fetch_articles и __main__."""

from pathlib import Path

import httpx

from markdownurl import fetch_article, fetch_articles


def _make_transport(text: str | None = None) -> httpx.MockTransport:
    """Создать мокированный транспорт."""
    if text is None:
        text = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Article</title>
            <meta name="author" content="Test Author">
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Test Article Title</h1>
            <p>This is a test paragraph with <a href="https://example.com/link">a link</a>.</p>
        </body>
        </html>
        """
    def handler(request):
        return httpx.Response(
            200,
            text=text,
            headers={"Content-Type": "text/html; charset=utf-8"},
        )
    return httpx.MockTransport(handler)


class TestFetchArticle:
    """Тесты функции fetch_article."""

    def test_fetch_article_success(self, tmp_path: Path) -> None:
        """Успешное извлечение статьи."""
        transport = _make_transport()
        output = tmp_path / "test.md"
        result = fetch_article(
            "https://example.com/article",
            output=str(output),
            transport=transport,
        )
        assert result.success is True
        assert result.filepath == output
        assert "test paragraph" in result.markdown.lower()

    def test_fetch_article_with_frontmatter(self, tmp_path: Path) -> None:
        """Извлечение с YAML-фронтматером."""
        transport = _make_transport()
        output = tmp_path / "fm.md"
        result = fetch_article(
            "https://example.com/article",
            output=str(output),
            include_frontmatter=True,
            transport=transport,
        )
        assert result.success is True
        assert result.frontmatter_yaml is not None
        assert result.frontmatter_yaml.startswith("---")

    def test_fetch_article_no_frontmatter(self, tmp_path: Path) -> None:
        """Извлечение без YAML-фронтматера."""
        transport = _make_transport()
        output = tmp_path / "nofm.md"
        result = fetch_article(
            "https://example.com/article",
            output=str(output),
            include_frontmatter=False,
            transport=transport,
        )
        assert result.success is True
        assert result.frontmatter_yaml == ""

    def test_fetch_article_with_wikilinks(self, tmp_path: Path) -> None:
        """Извлечение с wikilink-форматом ссылок."""
        transport = _make_transport()
        output = tmp_path / "wiki.md"
        result = fetch_article(
            "https://example.com/article",
            output=str(output),
            link_format="wikilink",
            transport=transport,
        )
        assert result.success is True

    def test_fetch_article_with_markdown_links(self, tmp_path: Path) -> None:
        """Извлечение с markdown-форматом ссылок."""
        transport = _make_transport()
        output = tmp_path / "md.md"
        result = fetch_article(
            "https://example.com/article",
            output=str(output),
            link_format="markdown",
            transport=transport,
        )
        assert result.success is True

    def test_fetch_article_with_block_ids(self, tmp_path: Path) -> None:
        """Извлечение с block IDs."""
        transport = _make_transport()
        output = tmp_path / "blocks.md"
        result = fetch_article(
            "https://example.com/article",
            output=str(output),
            block_ids=True,
            transport=transport,
        )
        assert result.success is True

    def test_fetch_article_skip_conflict(self, tmp_path: Path) -> None:
        """Извлечение при конфликте — skip."""
        output = tmp_path / "existing.md"
        output.write_text("existing content", encoding="utf-8")
        transport = _make_transport()
        result = fetch_article(
            "https://example.com/article",
            output=str(output),
            conflict="skip",
            transport=transport,
        )
        assert result.success is False
        assert result.status == "skip"

    def test_fetch_article_overwrite_conflict(self, tmp_path: Path) -> None:
        """Извлечение при конфликте — overwrite."""
        output = tmp_path / "existing.md"
        output.write_text("old content", encoding="utf-8")
        transport = _make_transport()
        result = fetch_article(
            "https://example.com/article",
            output=str(output),
            conflict="overwrite",
            transport=transport,
        )
        assert result.success is True

    def test_fetch_article_error_status(self) -> None:
        """Результат со статусом error при ошибке."""
        def handler_error(request):
            raise httpx.ConnectError("Connection refused")
        transport = httpx.MockTransport(handler_error)
        result = fetch_article(
            "https://example.com/fail",
            transport=transport,
        )
        assert result.success is False
        assert result.status == "error"

    def test_fetch_article_empty_content(self) -> None:
        """Извлечение пустого контента."""
        transport = _make_transport(text="<html><body></body></html>")
        result = fetch_article(
            "https://example.com/empty",
            output="/tmp/empty.md",
            transport=transport,
        )
        assert result.success is False
        assert result.status == "skip"


class TestFetchArticles:
    """Тесты функции fetch_articles."""

    def test_fetch_articles_multiple(self, tmp_path: Path) -> None:
        """Пакетное извлечение нескольких статей."""
        transport = _make_transport()
        output_dir = tmp_path / "articles"
        output_dir.mkdir()
        urls = [
            "https://example.com/a",
            "https://example.com/b",
        ]
        results = fetch_articles(
            urls,
            output_dir=str(output_dir),
            transport=transport,
        )
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_fetch_articles_single(self, tmp_path: Path) -> None:
        """Пакетное извлечение одной статьи."""
        transport = _make_transport()
        output_dir = tmp_path / "article"
        output_dir.mkdir()
        results = fetch_articles(
            ["https://example.com/single"],
            output_dir=str(output_dir),
            transport=transport,
        )
        assert len(results) == 1
        assert results[0].success is True

    def test_fetch_articles_with_delay(self, tmp_path: Path) -> None:
        """Пакетное извлечение с задержкой."""
        transport = _make_transport()
        output_dir = tmp_path / "delayed"
        output_dir.mkdir()
        results = fetch_articles(
            ["https://example.com/d1", "https://example.com/d2"],
            output_dir=str(output_dir),
            delay=0.0,
            transport=transport,
        )
        assert len(results) == 2


class TestMain:
    """Тесты __main__.py."""

    def test_main_module_exists(self) -> None:
        """Модуль __main__ существует."""
        import importlib.util
        spec = importlib.util.find_spec("markdownurl.__main__")
        assert spec is not None
