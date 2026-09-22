"""CLI-тесты MarkdownURL с мокированием HTTP через httpx.MockTransport."""

from pathlib import Path

import httpx
import pytest
from click.testing import CliRunner

from markdownurl.cli import cli


class TestCLI:
    """Тесты CLI-команды."""

    @pytest.fixture()
    def runner(self):
        return CliRunner()

    def test_cli_no_urls(self, runner: CliRunner) -> None:
        """CLI без URL-адресов показывает ошибку."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 2
        assert "URL" in result.output or "url" in result.output.lower()

    def test_cli_single_url(self, runner: CliRunner) -> None:
        """CLI с одним URL-адресом."""
        result = runner.invoke(cli, ["https://example.com/article", "--output", "/tmp/test-cli.md"])
        assert result.exit_code == 0
        assert "Сохранено" in result.output or "Saved" in result.output

    def test_cli_multiple_urls(self, runner: CliRunner) -> None:
        """CLI с несколькими URL-адресами."""
        result = runner.invoke(
            cli,
            ["https://example.com/a", "https://example.com/b", "--output", "/tmp/test-cli/"],
        )
        assert result.exit_code == 0

    def test_cli_from_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --from-file."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://example.com/a\n# comment\nhttps://example.com/b\n", encoding="utf-8")

        result = runner.invoke(
            cli,
            ["--from-file", str(urls_file), "--output", str(tmp_path / "output")],
        )
        assert result.exit_code == 0

    def test_cli_from_file_not_found(self, runner: CliRunner) -> None:
        """CLI с несуществующим --from-file."""
        result = runner.invoke(cli, ["--from-file", "/nonexistent/urls.txt"])
        assert result.exit_code == 2
        assert "not found" in result.output.lower() or "не найден" in result.output.lower()

    def test_cli_no_frontmatter(self, runner: CliRunner) -> None:
        """CLI с --no-frontmatter."""
        result = runner.invoke(
            cli,
            ["https://example.com/nofm", "--output", "/tmp/test-cli-nofm.md", "--no-frontmatter"],
        )
        assert result.exit_code == 0

    def test_cli_format_markdown(self, runner: CliRunner) -> None:
        """CLI с --link-format markdown."""
        result = runner.invoke(
            cli,
            ["https://example.com/md", "--output", "/tmp/test-cli-md.md", "--link-format", "markdown"],
        )
        assert result.exit_code == 0

    def test_cli_format_wikilink(self, runner: CliRunner) -> None:
        """CLI с --link-format wikilink."""
        result = runner.invoke(
            cli,
            ["https://example.com/wk", "--output", "/tmp/test-cli-wk.md", "--link-format", "wikilink"],
        )
        assert result.exit_code == 0

    def test_cli_images_skip(self, runner: CliRunner) -> None:
        """CLI с --images skip."""
        result = runner.invoke(
            cli,
            ["https://example.com/skip", "--output", "/tmp/test-cli-skip.md", "--images", "skip"],
        )
        assert result.exit_code == 0

    def test_cli_images_download(self, runner: CliRunner) -> None:
        """CLI с --images download (без реальных изображений — просто проверка без ошибок)."""
        result = runner.invoke(
            cli,
            ["https://example.com/down", "--output", "/tmp/test-cli-down.md", "--images", "download"],
        )
        assert result.exit_code == 0

    def test_cli_date_prefix(self, runner: CliRunner) -> None:
        """CLI с --date-prefix."""
        result = runner.invoke(
            cli,
            ["https://example.com/dp", "--output", "/tmp/test-cli-dp.md", "--date-prefix"],
        )
        assert result.exit_code == 0

    def test_cli_block_ids(self, runner: CliRunner) -> None:
        """CLI с --block-ids."""
        result = runner.invoke(
            cli,
            ["https://example.com/bi", "--output", "/tmp/test-cli-bi.md", "--block-ids"],
        )
        assert result.exit_code == 0

    def test_cli_conflict_suffix(self, runner: CliRunner) -> None:
        """CLI с --conflict suffix."""
        result = runner.invoke(
            cli,
            ["https://example.com/cs", "--output", "/tmp/test-cli-cs.md", "--conflict", "suffix"],
        )
        assert result.exit_code == 0

    def test_cli_conflict_overwrite(self, runner: CliRunner) -> None:
        """CLI с --conflict overwrite."""
        result = runner.invoke(
            cli,
            ["https://example.com/co", "--output", "/tmp/test-cli-co.md", "--conflict", "overwrite"],
        )
        assert result.exit_code == 0

    def test_cli_conflict_skip(self, runner: CliRunner) -> None:
        """CLI с --conflict skip."""
        result = runner.invoke(
            cli,
            ["https://example.com/csk", "--output", "/tmp/test-cli-csk.md", "--conflict", "skip"],
        )
        assert result.exit_code == 0

    def test_cli_timeout(self, runner: CliRunner) -> None:
        """CLI с --timeout."""
        result = runner.invoke(
            cli,
            ["https://example.com/to", "--output", "/tmp/test-cli-to.md", "--timeout", "5.0"],
        )
        assert result.exit_code == 0

    def test_cli_images_dir(self, runner: CliRunner) -> None:
        """CLI с --images-dir."""
        result = runner.invoke(
            cli,
            ["https://example.com/id", "--output", "/tmp/test-cli-id.md", "--images-dir", "myimages"],
        )
        assert result.exit_code == 0

    def test_cli_user_agent(self, runner: CliRunner) -> None:
        """CLI с --user-agent."""
        result = runner.invoke(
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

    def test_cli_help(self, runner: CliRunner) -> None:
        """CLI с --help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "MarkdownURL" in result.output

    def test_cli_404_error(self, runner: CliRunner) -> None:
        """CLI обрабатывает 404."""
        def handler_404(request):
            return httpx.Response(404, text="Not Found")
        transport = httpx.MockTransport(handler_404)
        from markdownurl.fetcher import Fetcher
        original_init = Fetcher.__init__
        def patched_init(self, *args, **kwargs):
            kwargs["transport"] = transport
            original_init(self, *args, **kwargs)
        Fetcher.__init__ = patched_init
        try:
            result = runner.invoke(
                cli,
                ["https://example.com/notfound", "--output", "/tmp/test-cli-404.md"],
            )
            # 404 — это skip, exit_code 0 или 4
            assert result.exit_code in (0, 4)
        finally:
            Fetcher.__init__ = original_init

    def test_cli_500_error(self, runner: CliRunner) -> None:
        """CLI обрабатывает 500."""
        def handler_500(request):
            return httpx.Response(500, text="Server Error")
        transport = httpx.MockTransport(handler_500)
        from markdownurl.fetcher import Fetcher
        original_init = Fetcher.__init__
        def patched_init(self, *args, **kwargs):
            kwargs["transport"] = transport
            original_init(self, *args, **kwargs)
        Fetcher.__init__ = patched_init
        try:
            result = runner.invoke(
                cli,
                ["https://example.com/error", "--output", "/tmp/test-cli-500.md"],
            )
            assert result.exit_code in (0, 5)
        finally:
            Fetcher.__init__ = original_init

    def test_cli_output_is_directory(self, runner: CliRunner) -> None:
        """CLI с --output как директория."""
        result = runner.invoke(
            cli,
            ["https://example.com/dir", "--output", "/tmp/test-cli-dir/"],
        )
        assert result.exit_code == 0

    def test_cli_output_no_extension(self, runner: CliRunner) -> None:
        """CLI с --output без расширения."""
        result = runner.invoke(
            cli,
            ["https://example.com/noext", "--output", "/tmp/test-cli-noext"],
        )
        assert result.exit_code == 0

    def test_cli_delay_between_requests(self, runner: CliRunner) -> None:
        """CLI с --delay между запросами."""
        result = runner.invoke(
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

    def test_cli_empty_content(self, runner: CliRunner) -> None:
        """CLI с пустым контентом."""
        def handler_empty(request):
            return httpx.Response(200, text="<html><body></body></html>")
        transport = httpx.MockTransport(handler_empty)
        from markdownurl.fetcher import Fetcher
        original_init = Fetcher.__init__
        def patched_init(self, *args, **kwargs):
            kwargs["transport"] = transport
            original_init(self, *args, **kwargs)
        Fetcher.__init__ = patched_init
        try:
            result = runner.invoke(
                cli,
                ["https://example.com/empty", "--output", "/tmp/test-cli-empty.md"],
            )
            assert result.exit_code == 0
        finally:
            Fetcher.__init__ = original_init

    def test_cli_combined_options(self, runner: CliRunner) -> None:
        """CLI с множеством опций."""
        result = runner.invoke(
            cli,
            [
                "https://example.com/combined",
                "--output",
                "/tmp/test-cli-combined.md",
                "--link-format",
                "markdown",
                "--images",
                "skip",
                "--no-frontmatter",
                "--timeout",
                "15.0",
            ],
        )
        assert result.exit_code == 0
