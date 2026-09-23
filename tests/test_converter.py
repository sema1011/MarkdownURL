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

    # TEST-2: Тесты для _convert_shell_commands
    def test_convert_shell_commands_simple(self) -> None:
        """Shell-команды оборачиваются в ```bash блоки."""
        text = "sudo apt update\npip install requests"
        result = self.converter._convert_shell_commands(text)
        assert "```bash" in result

    def test_convert_shell_commands_skips_code_blocks(self) -> None:
        """Содержимое ``` блоков не обрабатывается."""
        text = "```bash\nsudo apt update\n```\nsome text"
        result = self.converter._convert_shell_commands(text)
        lines = result.split("\n")
        # Должен быть только один ```bash (из исходного блока)
        assert lines.count("```bash") == 1

    def test_convert_shell_commands_empty_line(self) -> None:
        """Пустые строки не становятся shell-командами."""
        text = "sudo apt update\n\nsome text"
        result = self.converter._convert_shell_commands(text)
        assert "\n\n" in result

    # TEST-2: Тесты для _fix_html_lists
    def test_fix_html_lists_basic(self) -> None:
        """Восстановление простых списков по отступам."""
        text = "First item\n  Second item\n    Nested item"
        result = self.converter._fix_html_lists(text)
        # Элементы должны получить маркеры
        assert "-" in result or "*" in result or "+" in result

    def test_fix_html_lists_skips_marked(self) -> None:
        """Строки с существующими маркерами не обрабатываются."""
        text = "- Already marked\n  * Also marked"
        result = self.converter._fix_html_lists(text)
        assert "- Already marked" in result

    def test_fix_html_lists_preserves_code_blocks(self) -> None:
        """Содержимое ``` блоков не обрабатывается."""
        text = "```python\n- not a list\n```\n- real list"
        result = self.converter._fix_html_lists(text)
        assert "- real list" in result

    # TEST-2: Тесты для _convert_callouts
    def test_convert_callouts_note(self) -> None:
        """Конвертация callout типа note."""
        text = "> [!note] Important\n> This is a note"
        result = self.converter._convert_callouts(text)
        assert "> [!note]" in result

    def test_convert_callouts_warning(self) -> None:
        """Конвертация callout типа warning."""
        text = "> [!warning] Careful\n> This is a warning"
        result = self.converter._convert_callouts(text)
        assert "> [!warning]" in result

    def test_convert_callouts_escape_special_chars(self) -> None:
        """Спецсимволы > и ! в заголовке callout экранируются."""
        text = '> <blockquote class="info"><p>Title with > and ! chars</p><p>Content</p></blockquote>'
        result = self.converter._convert_callouts(text)
        # Спецсимволы должны быть экранированы
        assert "\\>" in result or "\\!" in result

    def test_convert_callouts_body_escape(self) -> None:
        """Спецсимволы в теле callout экранируются."""
        text = '> <blockquote class="info"><p>Title</p><p>Body with > quote and ! exclamation</p></blockquote>'
        result = self.converter._convert_callouts(text)
        # Спецсимволы должны быть экранированы
        assert "\\>" in result

    def test_convert_callouts_no_title(self) -> None:
        """Callout без заголовка."""
        text = "> [!tip]\n> Just content"
        result = self.converter._convert_callouts(text)
        assert "> [!tip]" in result

    def test_convert_callouts_regular_blockquote(self) -> None:
        """Обычный blockquote без класса остаётся без изменений."""
        text = "> Just a regular quote\n> Second line"
        result = self.converter._convert_callouts(text)
        assert "> Just a regular quote" in result

    # TEST-3: Тесты для _convert_function_params
    def test_convert_function_params_single(self) -> None:
        """Одиночный параметр функции."""
        text = "func(*param*)"
        result = self.converter._convert_function_params(text)
        assert "`param`" in result

    def test_convert_function_params_multiple(self) -> None:
        """Несколько параметров функции."""
        text = "func(*param1*, *param2*)"
        result = self.converter._convert_function_params(text)
        assert "`param1`" in result
        assert "`param2`" in result


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
