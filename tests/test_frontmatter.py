"""Тесты для модуля frontmatter — генерация YAML-фронтматера."""

from datetime import date

from markdownurl.extractor import ArticleMetadata
from markdownurl.frontmatter import FrontmatterGenerator


class TestFrontmatterGenerator:
    """Тесты класса FrontmatterGenerator."""

    def setup_method(self) -> None:
        self.generator = FrontmatterGenerator()

    def test_generate_minimal(self) -> None:
        meta = ArticleMetadata(title="Test Title")
        result = self.generator.generate(meta, "https://example.com")
        assert result.startswith("---")
        assert "title: Test Title" in result
        assert "source: https://example.com" in result
        assert result.endswith("---")

    def test_generate_with_all_fields(self) -> None:
        meta = ArticleMetadata(
            title="Test Title",
            author="Test Author",
            date="2026-09-22",
            description="Test description",
            tags=["tag1", "tag2"],
            og_title="OG Title",
        )
        result = self.generator.generate(meta, "https://example.com")
        assert "title: Test Title" in result
        assert "author: Test Author" in result
        assert "'2026-09-22'" in result or "date: 2026-09-22" in result
        assert "description: Test description" in result
        assert "aliases:" in result
        assert "- OG Title" in result

    def test_generate_without_frontmatter(self) -> None:
        meta = ArticleMetadata(title="Test")
        result = self.generator.generate(meta, "https://example.com", include_frontmatter=False)
        assert result == ""

    def test_generate_default_date(self) -> None:
        meta = ArticleMetadata(title="Test")
        result = self.generator.generate(meta, "https://example.com")
        today = date.today().isoformat()
        assert f"'{today}'" in result or f"date: {today}" in result

    def test_generate_default_tags(self) -> None:
        meta = ArticleMetadata(title="Test")
        result = self.generator.generate(meta, "https://example.com")
        assert "- web-clip" in result

    def test_generate_no_og_title_alias(self) -> None:
        meta = ArticleMetadata(title="Same Title", og_title="Same Title")
        result = self.generator.generate(meta, "https://example.com")
        assert "aliases:" not in result

    def test_generate_empty_title(self) -> None:
        meta = ArticleMetadata(title="")
        result = self.generator.generate(meta, "https://example.com")
        assert "title: Untitled" in result

    def test_generate_tags_list(self) -> None:
        meta = ArticleMetadata(title="Test", tags=["web-clip", "article"])
        result = self.generator.generate(meta, "https://example.com")
        assert "- web-clip" in result
        assert "- article" in result

    def test_generate_empty_tags(self) -> None:
        meta = ArticleMetadata(title="Test", tags=[])
        result = self.generator.generate(meta, "https://example.com")
        assert "- web-clip" in result


class TestToDict:
    """Тесты метода to_dict."""

    def setup_method(self) -> None:
        self.generator = FrontmatterGenerator()

    def test_to_dict_basic(self) -> None:
        meta = ArticleMetadata(title="Test", author="Author", date="2026-09-22")
        result = self.generator.to_dict(meta, "https://example.com")
        assert result["title"] == "Test"
        assert result["author"] == "Author"
        assert result["date"] == "2026-09-22"
        assert result["source"] == "https://example.com"

    def test_to_dict_default_tags(self) -> None:
        meta = ArticleMetadata(title="Test")
        result = self.generator.to_dict(meta, "https://example.com")
        assert result["tags"] == ["web-clip"]

    def test_to_dict_with_alias(self) -> None:
        meta = ArticleMetadata(title="Title", og_title="Different Title")
        result = self.generator.to_dict(meta, "https://example.com")
        assert result["aliases"] == ["Different Title"]
