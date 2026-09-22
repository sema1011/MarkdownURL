"""Тесты для основного API — fetch_article и ArticleResult."""

from markdownurl import ArticleResult


class TestArticleResult:
    """Тесты класса ArticleResult."""

    def test_success_property(self) -> None:
        result = ArticleResult(
            url="https://example.com",
            title="Test",
            markdown="Content",
            frontmatter={},
            status="success",
        )
        assert result.success is True

    def test_error_property(self) -> None:
        result = ArticleResult(
            url="https://example.com",
            title="",
            markdown="",
            frontmatter={},
            status="error",
        )
        assert result.success is False

    def test_skip_property(self) -> None:
        result = ArticleResult(
            url="https://example.com",
            title="",
            markdown="",
            frontmatter={},
            status="skip",
        )
        assert result.success is False

    def test_save_with_path(self, tmp_path: str) -> None:
        result = ArticleResult(
            url="https://example.com",
            title="Test",
            markdown="Content",
            frontmatter={},
            filepath=tmp_path / "test.md",
        )
        saved = result.save()
        assert saved.exists()

    def test_save_with_explicit_path(self, tmp_path: str) -> None:
        result = ArticleResult(
            url="https://example.com",
            title="Test",
            markdown="Content",
            frontmatter={},
            filepath=None,
        )
        target = tmp_path / "explicit.md"
        saved = result.save(target)
        assert saved == target

    def test_save_no_path_raises(self) -> None:
        result = ArticleResult(
            url="https://example.com",
            title="Test",
            markdown="Content",
            frontmatter={},
            filepath=None,
        )
        try:
            result.save()
            raise AssertionError("Expected ValueError")
        except ValueError:
            pass

    def test_frontmatter_to_yaml(self) -> None:
        result = ArticleResult(
            url="https://example.com",
            title="Test",
            markdown="Content",
            frontmatter={"title": "Test", "source": "https://example.com"},
        )
        yaml_str = result.frontmatter_to_yaml()
        assert yaml_str.startswith("---")
        assert "title:" in yaml_str


class TestArticleResultFrontmatterYaml:
    """Тесты кэширования YAML фронтматера."""

    def test_cached_frontmatter_yaml(self) -> None:
        yaml_content = "---\ntitle: Test\n---"
        result = ArticleResult(
            url="https://example.com",
            title="Test",
            markdown="Content",
            frontmatter={"title": "Test"},
            frontmatter_yaml=yaml_content,
        )
        assert result.frontmatter_to_yaml() == yaml_content

    def test_cached_yaml_takes_precedence(self) -> None:
        """Кэшированный YAML должен иметь приоритет."""
        cached = "---\ncached: true\n---"
        result = ArticleResult(
            url="https://example.com",
            title="Test",
            markdown="Content",
            frontmatter={"title": "Different"},
            frontmatter_yaml=cached,
        )
        assert result.frontmatter_to_yaml() == cached
        assert "cached: true" in result.frontmatter_to_yaml()
