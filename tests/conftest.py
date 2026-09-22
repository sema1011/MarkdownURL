"""Конфигурация тестов MarkdownURL."""

from pathlib import Path

import httpx
import pytest

from markdownurl.fetcher import Fetcher


@pytest.fixture()
def mock_transport():
    """Создать мокированный HTTP-транспорт для всех тестов."""
    def handler(request):
        return httpx.Response(
            200,
            text="""
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
            """,
            headers={"Content-Type": "text/html; charset=utf-8"},
        )
    return httpx.MockTransport(handler)


@pytest.fixture(autouse=True)
def _patch_fetcher_transport(mock_transport):
    """Автоматически внедрить mock_transport в Fetcher для всех тестов."""
    original_init = Fetcher.__init__

    def patched_init(self, *args, **kwargs):
        # Не переопределять transport, если он уже передан
        if "transport" not in kwargs or kwargs["transport"] is None:
            kwargs["transport"] = mock_transport
        original_init(self, *args, **kwargs)

    Fetcher.__init__ = patched_init
    yield
    Fetcher.__init__ = original_init


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    """Создать временную директорию для тестов."""
    return tmp_path


@pytest.fixture()
def sample_html() -> str:
    """Пример HTML-страницы для тестов."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Article</title>
        <meta name="author" content="Test Author">
        <meta name="description" content="Test description">
        <meta property="og:title" content="OG Title">
        <meta property="og:image" content="https://example.com/image.jpg">
    </head>
    <body>
        <h1>Test Article Title</h1>
        <p>This is a test paragraph with <a href="https://example.com">a link</a>.</p>
        <blockquote class="callout-info">
            <p>This is a callout block.</p>
        </blockquote>
        <img src="https://example.com/img.jpg" alt="Test Image">
    </body>
    </html>
    """


@pytest.fixture()
def sample_markdown() -> str:
    """Пример Markdown-контента для тестов."""
    return """# Test Article

This is a test paragraph with [a link](https://example.com).

> [!info] This is a callout block.
> Blockquote content here.

![Test Image](https://example.com/img.jpg)
"""


@pytest.fixture()
def sample_image_html() -> str:
    """HTML с изображениями для тестов."""
    return """
    <html>
    <body>
        <img src="https://example.com/photo.jpg" alt="Photo">
        <img src="https://example.com/logo.png" alt="Logo">
        <img src="https://example.com/icon.svg">
        <p>Some text with ![existing](https://example.com/exist.jpg) image.</p>
    </body>
    </html>
    """
