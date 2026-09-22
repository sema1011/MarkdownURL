"""Тесты для модуля converter — постобработка Markdown."""

from markdownurl.converter import Converter


class TestConverter:
    """Тесты класса Converter."""

    def setup_method(self) -> None:
        self.converter = Converter()

    def test_convert_highlights(self) -> None:
        text = "This is <mark>important</mark> text."
        result = self.converter._convert_highlights(text)
        assert result == "This is ==important== text."

    def test_convert_comments(self) -> None:
        text = "Visible <!-- hidden --> content"
        result = self.converter._convert_comments(text)
        assert result == "Visible %% hidden %% content"

    def test_convert_math_inline(self) -> None:
        text = "<math>x + y</math>"
        result = self.converter._convert_math(text)
        assert result == "$x + y$"

    def test_convert_math_block(self) -> None:
        text = '<math display="block">a^2 + b^2 = c^2</math>'
        result = self.converter._convert_math(text)
        assert result == "$$a^2 + b^2 = c^2$$"

    def test_convert_math_span(self) -> None:
        text = '<span class="math">E = mc^2</span>'
        result = self.converter._convert_math(text)
        assert result == "$E = mc^2$"

    def test_convert_math_nested(self) -> None:
        """Вложенный math внутри span class=math."""
        text = '<span class="math"><math>x</math></span>'
        result = self.converter._convert_math(text)
        # Сначала <math> → $x$, потом <span> → $$x$$
        assert result == "$$x$$"

    def test_convert_mermaid(self) -> None:
        text = '<pre class="mermaid">graph TD; A-->B;</pre>'
        result = self.converter._convert_mermaid(text)
        assert "```mermaid" in result
        assert "graph TD; A-->B;" in result

    def test_convert_wikilinks(self) -> None:
        text = "[Link](/internal/page)"
        result = self.converter._to_wikilinks(text)
        assert result == "[[Link]]"

    def test_convert_wikilinks_preserves_external_links(self) -> None:
        text = "[Link](https://example.com/page)"
        result = self.converter._to_wikilinks(text)
        assert result == text

    def test_convert_wikilinks_preserves_images(self) -> None:
        text = "![Image](https://example.com/img.jpg)"
        result = self.converter._to_wikilinks(text)
        assert result == text

    def test_convert_wikilinks_preserves_data_urls(self) -> None:
        text = "[Link](data:text/plain,hello)"
        result = self.converter._to_wikilinks(text)
        assert result == text

    def test_absolute_links(self) -> None:
        text = "[Link](relative/path)"
        result = self.converter._absolute_links(text, "https://example.com/base/")
        assert "https://example.com/base/relative/path" in result

    def test_absolute_links_preserves_external(self) -> None:
        text = "[Link](https://other.com/page)"
        result = self.converter._absolute_links(text, "https://example.com/")
        assert result == "[Link](https://other.com/page)"


class TestConvertMethod:
    """Тесты основного метода convert."""

    def setup_method(self) -> None:
        self.converter = Converter()

    def test_convert_basic(self) -> None:
        text = "Hello World"
        result = self.converter.convert(text)
        assert result == "Hello World"

    def test_convert_with_wikilinks(self) -> None:
        text = "[Link](/internal/page)"
        result = self.converter.convert(text, link_format="wikilink")
        assert "[[Link]]" in result

    def test_convert_with_markdown_links(self) -> None:
        text = "[Link](https://example.com)"
        result = self.converter.convert(text, link_format="markdown")
        assert "[Link](https://example.com)" in result

    def test_convert_with_block_ids(self) -> None:
        text = "Some paragraph\n\nAnother paragraph"
        result = self.converter.convert(text, block_ids=True)
        # Block IDs добавляются в конце параграфов
        assert "^" in result

    def test_convert_without_block_ids(self) -> None:
        text = "Some paragraph"
        result = self.converter.convert(text, block_ids=False)
        assert "^" not in result


class TestConvertCallouts:
    """Тесты конвертации callouts."""

    def setup_method(self) -> None:
        self.converter = Converter()

    def test_callout_detection(self) -> None:
        text = "> [!info] Title\n> Content"
        result = self.converter._convert_callouts(text)
        assert "> [!info]" in result

    def test_regular_blockquote(self) -> None:
        text = "> Just a regular quote"
        result = self.converter._convert_callouts(text)
        assert "> Just a regular quote" in result
