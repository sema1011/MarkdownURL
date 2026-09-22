"""Извлечение контента и метаданных из HTML-страницы."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser

import trafilatura
from bs4 import BeautifulSoup


@dataclass
class ArticleMetadata:
    """Метаданные статьи."""

    title: str = ""
    author: str = ""
    date: str = ""  # ISO 8601 YYYY-MM-DD
    description: str = ""
    tags: list[str] = field(default_factory=list)
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""


@dataclass
class ImageInfo:
    """Информация об изображении."""

    src: str
    alt: str = ""
    width: int | None = None
    height: int | None = None


class ImageParser(HTMLParser):
    """Извлекает информацию об изображениях из HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.images: list[ImageInfo] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "img":
            return

        attrs_dict: dict[str, str | None] = {}
        for name, value in attrs:
            attrs_dict[name] = value

        src = attrs_dict.get("src", "") or attrs_dict.get("data-src", "")
        if not src:
            return

        alt = attrs_dict.get("alt", "") or ""

        width: int | None = None
        height: int | None = None
        w = attrs_dict.get("width")
        h = attrs_dict.get("height")
        if w and w.isdigit():
            width = int(w)
        if h and h.isdigit():
            height = int(h)

        self.images.append(ImageInfo(src=src, alt=alt, width=width, height=height))


def _parse_date(raw: str | None) -> str:
    """Парсить дату из различных форматов в ISO 8601 (YYYY-MM-DD)."""
    if not raw:
        return ""

    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return ""


def _clean_text(text: str) -> str:
    """Очистить текст от спецсимволов и лишних пробелов."""
    text = re.sub(r'[^\w\s\-_\'.+]', '', text, flags=re.UNICODE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_meta_tags(soup: BeautifulSoup, html: str) -> ArticleMetadata:
    """Извлечь метаданные из HTML-тегов и meta-элементов."""
    meta = ArticleMetadata()

    # title: h1 > title > og:title
    h1 = soup.find("h1")
    if h1:
        meta.title = _clean_text(h1.get_text(strip=True))

    page_title = soup.title
    if page_title and page_title.string:
        title_text = _clean_text(page_title.string.strip())
        if title_text and not meta.title:
            meta.title = title_text

    # og:title
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        meta.og_title = _clean_text(og_title["content"].strip())
        if not meta.title:
            meta.title = meta.og_title

    # author
    author_meta = (
        soup.find("meta", attrs={"name": "author"})
        or soup.find("meta", property="article:author")
    )
    if author_meta and author_meta.get("content"):
        meta.author = author_meta["content"].strip()

    # article:author (schema.org fallback)
    if not meta.author:
        author_elem = soup.find("meta", attrs={"itemprop": "author"})
        if author_elem and author_elem.get("content"):
            meta.author = author_elem["content"].strip()

    # date
    date_meta = (
        soup.find("meta", property="article:published_time")
        or soup.find("meta", attrs={"name": "date"})
        or soup.find("meta", attrs={"name": "publishdate"})
        or soup.find("meta", attrs={"name": "publication_date"})
    )
    if date_meta and date_meta.get("content"):
        meta.date = _parse_date(date_meta["content"])

    # fallback: <time>
    if not meta.date:
        time_elem = soup.find("time", attrs={"datetime": True})
        if time_elem:
            meta.date = _parse_date(time_elem["datetime"])

    # description
    desc_meta = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", property="og:description")
    )
    if desc_meta and desc_meta.get("content"):
        meta.description = desc_meta["content"].strip()

    # tags / keywords
    keywords_meta = soup.find("meta", attrs={"name": "keywords"})
    if keywords_meta and keywords_meta.get("content"):
        meta.tags = [
            t.strip() for t in keywords_meta["content"].split(",") if t.strip()
        ]

    # og:image
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        meta.og_image = og_image["content"].strip()

    return meta


def _extract_images(html: str) -> list[ImageInfo]:
    """Извлечь информацию об изображениях из HTML."""
    parser = ImageParser()
    parser.feed(html)
    return parser.images


class Extractor:
    """Извлечение контента и метаданных из HTML."""

    def extract(self, html: str, url: str = "") -> tuple[str, ArticleMetadata, list[ImageInfo]]:
        """Извлечь markdown-контент и метаданные из HTML.

        Args:
            html: Исходный HTML-код страницы.
            url: URL страницы (для trafilatura).

        Returns:
            Кортеж (markdown_content, metadata, images).
        """
        # Извлечение контента через trafilatura
        markdown = trafilatura.extract(
            html,
            output_format="markdown",
            include_comments=False,
            include_tables=True,
            favor_precision=True,
        )

        if not markdown or not markdown.strip():
            markdown = ""

        # Парсинг HTML для метаданных и специфичных элементов
        soup = BeautifulSoup(html, "lxml")
        meta = _extract_meta_tags(soup, html)
        images = _extract_images(html)

        return markdown, meta, images
