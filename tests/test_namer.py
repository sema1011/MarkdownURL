"""Тесты для модуля namer — генерация имён файлов."""

from pathlib import Path

from markdownurl.namer import Namer


class TestSlugify:
    """Тесты метода slugify."""

    def test_simple_text(self) -> None:
        namer = Namer()
        assert namer.slugify("Hello World") == "hello-world"

    def test_with_html_tags(self) -> None:
        namer = Namer()
        assert namer.slugify("<b>Bold Text</b>") == "bold-text"

    def test_with_special_characters(self) -> None:
        namer = Namer()
        assert namer.slugify("Test & More") == "test-more"

    def test_with_unicode(self) -> None:
        namer = Namer()
        assert namer.slugify("Привет Мир") == "привет-мир"

    def test_with_html_entities(self) -> None:
        namer = Namer()
        # &amp; → & → удаляется regex [^\w\s\-_]
        assert namer.slugify("C++ &amp; Python") == "c-python"

    def test_multiple_spaces(self) -> None:
        namer = Namer()
        assert namer.slugify("Hello    World") == "hello-world"

    def test_leading_trailing_hyphens(self) -> None:
        namer = Namer()
        assert namer.slugify("---Test---") == "test"

    def test_forbidden_characters_removed(self) -> None:
        namer = Namer()
        assert namer.slugify("Test[1]#2^3|4") == "test1234"

    def test_empty_text(self) -> None:
        namer = Namer()
        assert namer.slugify("") == ""


class TestGenerateName:
    """Тесты метода generate_name."""

    def test_basic_generation(self) -> None:
        namer = Namer()
        result = namer.generate_name("My Article")
        assert result == "my-article.md"

    def test_with_date_prefix(self) -> None:
        namer = Namer(date_prefix=True)
        result = namer.generate_name("My Article", date_str="2026-09-22")
        assert result == "2026-09-22-my-article.md"

    def test_no_date_prefix(self) -> None:
        namer = Namer(date_prefix=False)
        result = namer.generate_name("My Article", date_str="2026-09-22")
        assert result == "my-article.md"

    def test_empty_title(self) -> None:
        namer = Namer()
        result = namer.generate_name("")
        assert result == ".md"

    def test_url_affects_truncation(self) -> None:
        namer = Namer()
        # URL используется для уникальности при обрезке
        result = namer.generate_name("Test", url="https://example.com/1")
        assert result.endswith(".md")


class TestTruncate:
    """Тесты метода _truncate."""

    def test_short_slug_not_truncated(self) -> None:
        namer = Namer()
        result = namer._truncate("short", "https://example.com")
        assert result == "short"

    def test_long_slug_truncated(self) -> None:
        namer = Namer()
        long_text = "a" * 100
        result = namer._truncate(long_text, "https://example.com")
        assert len(result) <= namer.MAX_LENGTH
        assert "…" in result

    def test_long_slug_without_url(self) -> None:
        namer = Namer()
        long_text = "a" * 100
        result = namer._truncate(long_text, "")
        assert len(result) <= namer.MAX_LENGTH
        assert "…" in result


class TestResolveConflict:
    """Тесты метода resolve_conflict."""

    def test_new_file(self, tmp_path: Path) -> None:
        namer = Namer()
        filepath = tmp_path / "new-file.md"
        result, action = namer.resolve_conflict(filepath)
        assert action == "new"
        assert result == filepath

    def test_overwrite_conflict(self, tmp_path: Path) -> None:
        filepath = tmp_path / "existing.md"
        filepath.touch()
        namer = Namer(on_conflict="overwrite")
        result, action = namer.resolve_conflict(filepath)
        assert action == "overwrite"

    def test_skip_conflict(self, tmp_path: Path) -> None:
        filepath = tmp_path / "existing.md"
        filepath.touch()
        namer = Namer(on_conflict="skip")
        result, action = namer.resolve_conflict(filepath)
        assert action == "skip"

    def test_suffix_conflict(self, tmp_path: Path) -> None:
        filepath = tmp_path / "existing.md"
        filepath.touch()
        namer = Namer(on_conflict="suffix")
        result, action = namer.resolve_conflict(filepath)
        assert action == "suffixed"
        assert "existing-2.md" in str(result)


class TestResolveConflictDownload:
    """Тесты метода resolve_conflict_download."""

    def test_unique_filename(self) -> None:
        namer = Namer()
        result = namer.resolve_conflict_download("photo.jpg", set())
        assert result == "photo.jpg"

    def test_duplicate_filename(self) -> None:
        namer = Namer()
        result = namer.resolve_conflict_download("photo.jpg", {"photo.jpg"})
        assert result == "photo-2.jpg"

    def test_duplicate_with_suffix(self) -> None:
        namer = Namer()
        existing = {"photo.jpg", "photo-2.jpg"}
        result = namer.resolve_conflict_download("photo.jpg", existing)
        assert result == "photo-3.jpg"

    def test_overwrite_mode(self) -> None:
        namer = Namer(on_conflict="overwrite")
        result = namer.resolve_conflict_download("photo.jpg", {"photo.jpg"})
        assert result == "photo.jpg"

    def test_skip_mode(self) -> None:
        namer = Namer(on_conflict="skip")
        result = namer.resolve_conflict_download("photo.jpg", {"photo.jpg"})
        assert result == ""

    def test_no_extension(self) -> None:
        namer = Namer()
        result = namer.resolve_conflict_download("photo", {"photo"})
        assert result == "photo-2"


class TestSplitStemExt:
    """Тесты метода _split_stem_ext."""

    def test_with_extension(self) -> None:
        stem, ext = Namer._split_stem_ext("photo.jpg")
        assert stem == "photo"
        assert ext == ".jpg"

    def test_without_extension(self) -> None:
        stem, ext = Namer._split_stem_ext("photo")
        assert stem == "photo"
        assert ext == ""

    def test_multiple_dots(self) -> None:
        stem, ext = Namer._split_stem_ext("file.tar.gz")
        assert stem == "file.tar"
        assert ext == ".gz"
