"""CLI-тесты MarkdownURL с мокированием HTTP через respx."""

from pathlib import Path

import httpx
import respx
from click.testing import CliRunner

from markdownurl.cli import cli


SAMPLE_HTML = """
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
"""


def _make_response(text: str = SAMPLE_HTML) -> httpx.Response:
    """Создать мокированный HTTP-ответ."""
    return httpx.Response(200, text=text, headers={"Content-Type": "text/html; charset=utf-8"})


class TestCLI:
    """Тесты CLI-команды."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @respx.mock
    def test_cli_no_urls(self) -> None:
        """CLI без URL-адресов показывает ошибку."""
        result = self.runner.invoke(cli, [])
        assert result.exit_code == 2
        assert "URL" in result.output or "url" in result.output.lower()

    @respx.mock
    def test_cli_single_url(self) -> None:
        """CLI с одним URL-адресом."""
        respx.get("https://example.com/article").mock(return_value=_make_response())

        result = self.runner.invoke(cli, ["https://example.com/article", "--output", "/tmp/test-cli.md"])
        assert result.exit_code == 0
        assert "Сохранено" in result.output or "Saved" in result.output

    @respx.mock
    def test_cli_multiple_urls(self) -> None:
        """CLI с несколькими URL-адресами."""
        for url in ["https://example.com/a", "https://example.com/b"]:
            respx.get(url).mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/a", "https://example.com/b", "--output", "/tmp/test-cli/"],
        )
        assert result.exit_code == 0
        assert "Готово" in result.output or "Done" in result.output
        assert "2 успешно" in result.output or "2 OK" in result.output

    @respx.mock
    def test_cli_from_file(self, tmp_path: Path) -> None:
        """CLI с --from-file."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://example.com/a\n# comment\nhttps://example.com/b\n", encoding="utf-8")

        for url in ["https://example.com/a", "https://example.com/b"]:
            respx.get(url).mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["--from-file", str(urls_file), "--output", str(tmp_path / "output")],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_from_file_not_found(self) -> None:
        """CLI с несуществующим --from-file."""
        result = self.runner.invoke(cli, ["--from-file", "/nonexistent/urls.txt"])
        assert result.exit_code == 2
        assert "найден" in result.output.lower()

    @respx.mock
    def test_cli_no_frontmatter(self) -> None:
        """CLI с --no-frontmatter."""
        respx.get("https://example.com/nofm").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/nofm", "--output", "/tmp/test-cli-nofm.md", "--no-frontmatter"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_format_markdown(self) -> None:
        """CLI с --format markdown."""
        respx.get("https://example.com/md").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/md", "--output", "/tmp/test-cli-md.md", "--format", "markdown"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_format_wikilink(self) -> None:
        """CLI с --format wikilink."""
        respx.get("https://example.com/wk").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/wk", "--output", "/tmp/test-cli-wk.md", "--format", "wikilink"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_images_skip(self) -> None:
        """CLI с --images skip."""
        respx.get("https://example.com/skip").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/skip", "--output", "/tmp/test-cli-skip.md", "--images", "skip"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_images_download(self) -> None:
        """CLI с --images download (без реальных изображений — просто проверка без ошибок)."""
        respx.get("https://example.com/down").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/down", "--output", "/tmp/test-cli-down.md", "--images", "download"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_date_prefix(self) -> None:
        """CLI с --date-prefix."""
        respx.get("https://example.com/dp").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/dp", "--output", "/tmp/test-cli-dp.md", "--date-prefix"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_block_ids(self) -> None:
        """CLI с --block-ids."""
        respx.get("https://example.com/bi").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/bi", "--output", "/tmp/test-cli-bi.md", "--block-ids"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_conflict_suffix(self) -> None:
        """CLI с --conflict suffix."""
        respx.get("https://example.com/cs").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/cs", "--output", "/tmp/test-cli-cs.md", "--conflict", "suffix"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_conflict_overwrite(self) -> None:
        """CLI с --conflict overwrite."""
        respx.get("https://example.com/co").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/co", "--output", "/tmp/test-cli-co.md", "--conflict", "overwrite"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_conflict_skip(self) -> None:
        """CLI с --conflict skip."""
        respx.get("https://example.com/csk").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/csk", "--output", "/tmp/test-cli-csk.md", "--conflict", "skip"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_timeout(self) -> None:
        """CLI с --timeout."""
        respx.get("https://example.com/to").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/to", "--output", "/tmp/test-cli-to.md", "--timeout", "5.0"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_images_dir(self) -> None:
        """CLI с --images-dir."""
        respx.get("https://example.com/id").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/id", "--output", "/tmp/test-cli-id.md", "--images-dir", "myimages"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_user_agent(self) -> None:
        """CLI с --user-agent."""
        respx.get("https://example.com/ua").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            [
                "https://example.com/ua",
                "--output",
                "/tmp/test-cli-ua.md",
                "--user-agent",
                "TestBot/1.0",
            ],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_help(self) -> None:
        """CLI --help показывает справку."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "MarkdownURL" in result.output
        assert "--output" in result.output
        assert "--from-file" in result.output
        assert "--images" in result.output
        assert "--format" in result.output

    @respx.mock
    def test_cli_404_error(self) -> None:
        """CLI обрабатывает 404."""
        respx.get("https://example.com/notfound").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        result = self.runner.invoke(
            cli,
            ["https://example.com/notfound", "--output", "/tmp/test-cli-404.md"],
        )
        # 404 — это skip, exit_code 0 или 4
        assert result.exit_code in (0, 4)

    @respx.mock
    def test_cli_500_error(self) -> None:
        """CLI обрабатывает 500."""
        respx.get("https://example.com/error").mock(
            return_value=httpx.Response(500, text="Server Error")
        )

        result = self.runner.invoke(
            cli,
            ["https://example.com/error", "--output", "/tmp/test-cli-500.md"],
        )
        assert result.exit_code in (0, 5)

    @respx.mock
    def test_cli_output_is_directory(self) -> None:
        """CLI с --output как директория."""
        respx.get("https://example.com/dir").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/dir", "--output", "/tmp/test-cli-dir/"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_output_no_extension(self) -> None:
        """CLI с --output без расширения."""
        respx.get("https://example.com/noext").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            ["https://example.com/noext", "--output", "/tmp/test-cli-noext"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_delay_between_requests(self) -> None:
        """CLI с --delay между запросами."""
        for url in ["https://example.com/d1", "https://example.com/d2"]:
            respx.get(url).mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            [
                "https://example.com/d1",
                "https://example.com/d2",
                "--output",
                "/tmp/test-cli-delay/",
                "--delay",
                "0.1",
            ],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_empty_content(self) -> None:
        """CLI с пустым контентом."""
        respx.get("https://example.com/empty").mock(
            return_value=httpx.Response(200, text="<html><body></body></html>")
        )

        result = self.runner.invoke(
            cli,
            ["https://example.com/empty", "--output", "/tmp/test-cli-empty.md"],
        )
        assert result.exit_code == 0

    @respx.mock
    def test_cli_combined_options(self) -> None:
        """CLI с множеством опций."""
        respx.get("https://example.com/combined").mock(return_value=_make_response())

        result = self.runner.invoke(
            cli,
            [
                "https://example.com/combined",
                "--output",
                "/tmp/test-cli-combined.md",
                "--format",
                "markdown",
                "--images",
                "skip",
                "--no-frontmatter",
                "--timeout",
                "15.0",
            ],
        )
        assert result.exit_code == 0
