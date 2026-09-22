"""Конфигурация тестов MarkdownURL."""

import tempfile
from pathlib import Path

import pytest


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
