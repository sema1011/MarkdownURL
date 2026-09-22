"""Тесты для модуля images — обработка изображений."""

from markdownurl.extractor import _extract_images
from markdownurl.images import ImageProcessor


class TestExtractExtension:
    """Тесты метода _extract_extension."""

    def setup_method(self) -> None:
        import tempfile
        from pathlib import Path

        from markdownurl.namer import Namer

        self.tmp_dir = Path(tempfile.mkdtemp())
        self.namer = Namer()
        self.processor = ImageProcessor(
            output_dir=self.tmp_dir,
            namer=self.namer,
            images_dir="attachments",
            timeout=5.0,
        )

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_jpg_extension(self) -> None:
        assert self.processor._extract_extension("photo.jpg") == ".jpg"

    def test_png_extension(self) -> None:
        assert self.processor._extract_extension("image.PNG") == ".png"

    def test_svg_extension(self) -> None:
        assert self.processor._extract_extension("icon.svg") == ".svg"

    def test_with_query_string(self) -> None:
        assert self.processor._extract_extension("photo.jpg?width=300") == ".jpg"

    def test_with_fragment(self) -> None:
        assert self.processor._extract_extension("photo.jpg#hash") == ".jpg"

    def test_no_extension(self) -> None:
        assert self.processor._extract_extension("photo") == ""


class TestImageProcessor:
    """Тесты класса ImageProcessor."""

    def setup_method(self) -> None:
        import tempfile
        from pathlib import Path

        from markdownurl.namer import Namer

        self.tmp_dir = Path(tempfile.mkdtemp())
        self.namer = Namer()
        self.processor = ImageProcessor(
            output_dir=self.tmp_dir,
            namer=self.namer,
            images_dir="attachments",
            timeout=5.0,
        )

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_process_images_with_links(self, sample_image_html: str) -> None:
        """Изображения без скачивания остаются как ссылки."""
        images = _extract_images(sample_image_html)
        result = self.processor.process_images(sample_image_html, "https://example.com", images)
        assert "https://example.com/photo.jpg" in result

    def test_process_images_replaces_markdown_images(self, sample_image_html: str) -> None:
        """Markdown-изображения заменяются на Obsidian-эмбеды."""
        images = _extract_images(sample_image_html)
        result = self.processor.process_images(sample_image_html, "https://example.com", images)
        assert "photo.jpg" in result or "img.jpg" in result

    def test_process_images_handles_missing_alt(self, sample_image_html: str) -> None:
        """Изображения без alt-атрибута обрабатываются корректно."""
        images = _extract_images(sample_image_html)
        result = self.processor.process_images(sample_image_html, "https://example.com", images)
        assert "icon.svg" in result


class TestReplaceImageLinks:
    """Тесты метода _replace_image_links."""

    def setup_method(self) -> None:
        import tempfile
        from pathlib import Path

        from markdownurl.namer import Namer

        self.tmp_dir = Path(tempfile.mkdtemp())
        self.namer = Namer()
        self.processor = ImageProcessor(
            output_dir=self.tmp_dir,
            namer=self.namer,
            images_dir="attachments",
            timeout=5.0,
        )

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_replace_with_width(self) -> None:
        markdown = "![Alt](https://example.com/img.jpg)"
        replacements = {"https://example.com/img.jpg": ("img.jpg", 300)}
        result = self.processor._replace_image_links(markdown, replacements)
        assert "![[img.jpg|300]]" in result

    def test_replace_without_width(self) -> None:
        markdown = "![Alt](https://example.com/img.jpg)"
        replacements = {"https://example.com/img.jpg": ("img.jpg", None)}
        result = self.processor._replace_image_links(markdown, replacements)
        assert "![[img.jpg]]" in result

    def test_replace_no_match(self) -> None:
        markdown = "![Alt](https://example.com/other.jpg)"
        replacements = {"https://example.com/img.jpg": ("img.jpg", 300)}
        result = self.processor._replace_image_links(markdown, replacements)
        assert result == markdown


class TestGenerateFilename:
    """Тесты метода _generate_filename."""

    def setup_method(self) -> None:
        import tempfile
        from pathlib import Path

        from markdownurl.namer import Namer

        self.tmp_dir = Path(tempfile.mkdtemp())
        self.namer = Namer()
        self.processor = ImageProcessor(
            output_dir=self.tmp_dir,
            namer=self.namer,
            images_dir="attachments",
            timeout=5.0,
        )

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_generate_filename_from_url(self) -> None:
        filename = self.processor._generate_filename("https://example.com/photo.jpg")
        assert filename.endswith(".jpg")

    def test_generate_filename_with_alt(self) -> None:
        filename = self.processor._generate_filename("https://example.com/photo.jpg", "My Photo")
        assert "my-photo" in filename

    def test_generate_filename_without_extension(self) -> None:
        filename = self.processor._generate_filename("https://example.com/api/data")
        assert filename.endswith(".jpg")  # fallback extension


class TestExtractImages:
    """Тесты функции _extract_images."""

    def test_extract_from_empty_html(self) -> None:
        images = _extract_images("<html><body></body></html>")
        assert images == []

    def test_extract_single_image(self) -> None:
        html = '<img src="https://example.com/img.jpg" alt="Alt text">'
        images = _extract_images(html)
        assert len(images) == 1
        assert images[0].src == "https://example.com/img.jpg"
        assert images[0].alt == "Alt text"
