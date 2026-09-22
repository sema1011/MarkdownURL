"""Тесты для модуля extractor — извлечение контента."""

from markdownurl.extractor import (
    ArticleMetadata,
    Extractor,
    ImageInfo,
    _extract_images,
    _extract_meta_tags,
    _parse_date,
)
from bs4 import BeautifulSoup


class TestArticleMetadata:
    """Тесты класса ArticleMetadata."""

    def test_default_values(self) -> None:
        meta = ArticleMetadata()
        assert meta.title == ""
        assert meta.author == ""
        assert meta.date == ""
        assert meta.tags == []

    def test_custom_values(self) -> None:
        meta = ArticleMetadata(title="Test", author="Author", date="2026-09-22")
        assert meta.title == "Test"
        assert meta.author == "Author"
        assert meta.date == "2026-09-22"


class TestImageInfo:
    """Тесты класса ImageInfo."""

    def test_default_values(self) -> None:
        info = ImageInfo(src="https://example.com/img.jpg")
        assert info.src == "https://example.com/img.jpg"
        assert info.alt == ""
        assert info.width is None
        assert info.height is None

    def test_with_all_fields(self) -> None:
        info = ImageInfo(src="url", alt="Alt", width=100, height=200)
        assert info.src == "url"
        assert info.alt == "Alt"
        assert info.width == 100
        assert info.height == 200


class TestExtractImages:
    """Тесты функции _extract_images."""

    def test_extract_images_from_html(self, sample_image_html: str) -> None:
        images = _extract_images(sample_image_html)
        assert len(images) == 3

    def test_extract_image_with_alt(self, sample_image_html: str) -> None:
        images = _extract_images(sample_image_html)
        photo = images[0]
        assert photo.src == "https://example.com/photo.jpg"
        assert photo.alt == "Photo"

    def test_extract_image_without_alt(self, sample_image_html: str) -> None:
        images = _extract_images(sample_image_html)
        icon = images[2]
        assert icon.src == "https://example.com/icon.svg"
        assert icon.alt == ""


class TestExtractMetaTags:
    """Тесты функции _extract_meta_tags."""

    def test_extract_basic_meta(self, sample_html: str) -> None:
        soup = BeautifulSoup(sample_html, "lxml")
        meta = _extract_meta_tags(soup, sample_html)
        assert meta.title == "Test Article Title"
        assert meta.author == "Test Author"
        assert meta.description == "Test description"

    def test_extract_og_title(self, sample_html: str) -> None:
        soup = BeautifulSoup(sample_html, "lxml")
        meta = _extract_meta_tags(soup, sample_html)
        assert meta.og_title == "OG Title"

    def test_extract_og_image(self, sample_html: str) -> None:
        soup = BeautifulSoup(sample_html, "lxml")
        meta = _extract_meta_tags(soup, sample_html)
        assert meta.og_image == "https://example.com/image.jpg"

    def test_extract_missing_author(self) -> None:
        html = "<html><head><title>Test</title></head><body></body></html>"
        soup = BeautifulSoup(html, "lxml")
        meta = _extract_meta_tags(soup, html)
        assert meta.author == ""


class TestParseDate:
    """Тесты функции _parse_date."""

    def test_iso_format(self) -> None:
        assert _parse_date("2026-09-22") == "2026-09-22"

    def test_datetime_format(self) -> None:
        result = _parse_date("2026-09-22T10:30:00+03:00")
        assert "2026-09-22" in result

    def test_none_input(self) -> None:
        assert _parse_date(None) == ""

    def test_empty_input(self) -> None:
        assert _parse_date("") == ""


class TestExtractor:
    """Тесты класса Extractor."""

    def setup_method(self) -> None:
        self.extractor = Extractor()

    def test_extract_returns_tuple(self, sample_html: str) -> None:
        result = self.extractor.extract(sample_html, "https://example.com")
        assert isinstance(result, tuple)
        assert len(result) == 3  # (markdown, meta, images)

    def test_extract_returns_markdown(self, sample_html: str) -> None:
        markdown, meta, images = self.extractor.extract(sample_html, "https://example.com")
        assert isinstance(markdown, str)
        assert "Test Article" in markdown or "test" in markdown.lower()

    def test_extract_returns_metadata(self, sample_html: str) -> None:
        markdown, meta, images = self.extractor.extract(sample_html, "https://example.com")
        assert isinstance(meta, ArticleMetadata)
        assert meta.title == "Test Article Title"

    def test_extract_returns_images(self, sample_html: str) -> None:
        markdown, meta, images = self.extractor.extract(sample_html, "https://example.com")
        assert isinstance(images, list)
        assert len(images) >= 1

    def test_extract_empty_html(self) -> None:
        markdown, meta, images = self.extractor.extract("<html><body></body></html>")
        assert markdown == ""
