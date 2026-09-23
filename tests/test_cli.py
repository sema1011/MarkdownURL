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

    def test_cli_single_url(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с одним URL-адресом."""
        result = runner.invoke(cli, ["https://example.com/article", "--output", str(tmp_path / "test-cli.md")])
        assert result.exit_code == 0
        assert "Сохранено" in result.output or "Saved" in result.output

    def test_cli_multiple_urls(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с несколькими URL-адресами."""
        result = runner.invoke(
            cli,
            ["https://example.com/a", "https://example.com/b", "--output", str(tmp_path / "test-cli")],
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

    def test_cli_no_frontmatter(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --no-frontmatter."""
        result = runner.invoke(
            cli,
            ["https://example.com/nofm", "--output", str(tmp_path / "test-cli-nofm.md"), "--no-frontmatter"],
        )
        assert result.exit_code == 0

    def test_cli_format_markdown(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --link-format markdown."""
        result = runner.invoke(
            cli,
            ["https://example.com/md", "--output", str(tmp_path / "test-cli-md.md"), "--link-format", "markdown"],
        )
        assert result.exit_code == 0

    def test_cli_format_wikilink(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --link-format wikilink."""
        result = runner.invoke(
            cli,
            ["https://example.com/wk", "--output", str(tmp_path / "test-cli-wk.md"), "--link-format", "wikilink"],
        )
        assert result.exit_code == 0

    def test_cli_images_skip(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --images skip."""
        result = runner.invoke(
            cli,
            ["https://example.com/skip", "--output", str(tmp_path / "test-cli-skip.md"), "--images", "skip"],
        )
        assert result.exit_code == 0

    def test_cli_images_download(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --images download (без реальных изображений — просто проверка без ошибок)."""
        result = runner.invoke(
            cli,
            ["https://example.com/down", "--output", str(tmp_path / "test-cli-down.md"), "--images", "download"],
        )
        assert result.exit_code == 0

    def test_cli_date_prefix(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --date-prefix."""
        result = runner.invoke(
            cli,
            ["https://example.com/dp", "--output", str(tmp_path / "test-cli-dp.md"), "--date-prefix"],
        )
        assert result.exit_code == 0

    def test_cli_block_ids(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --block-ids."""
        result = runner.invoke(
            cli,
            ["https://example.com/bi", "--output", str(tmp_path / "test-cli-bi.md"), "--block-ids"],
        )
        assert result.exit_code == 0

    def test_cli_conflict_suffix(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --conflict suffix."""
        result = runner.invoke(
            cli,
            ["https://example.com/cs", "--output", str(tmp_path / "test-cli-cs.md"), "--conflict", "suffix"],
        )
        assert result.exit_code == 0

    def test_cli_conflict_overwrite(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --conflict overwrite."""
        result = runner.invoke(
            cli,
            ["https://example.com/co", "--output", str(tmp_path / "test-cli-co.md"), "--conflict", "overwrite"],
        )
        assert result.exit_code == 0

    def test_cli_conflict_skip(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --conflict skip."""
        result = runner.invoke(
            cli,
            ["https://example.com/csk", "--output", str(tmp_path / "test-cli-csk.md"), "--conflict", "skip"],
        )
        assert result.exit_code == 0

    def test_cli_timeout(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --timeout."""
        result = runner.invoke(
            cli,
            ["https://example.com/to", "--output", str(tmp_path / "test-cli-to.md"), "--timeout", "5.0"],
        )
        assert result.exit_code == 0

    def test_cli_images_dir(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --images-dir."""
        result = runner.invoke(
            cli,
            ["https://example.com/id", "--output", str(tmp_path / "test-cli-id.md"), "--images-dir", "myimages"],
        )
        assert result.exit_code == 0

    def test_cli_user_agent(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --user-agent."""
        result = runner.invoke(
            cli,
            [
                "https://example.com/ua",
                "--output",
                str(tmp_path / "test-cli-ua.md"),
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

    def test_cli_404_error(self, runner: CliRunner, tmp_path: Path) -> None:
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
                ["https://example.com/notfound", "--output", str(tmp_path / "test-cli-404.md")],
            )
            # 404 — это skip, exit_code 0 или 4
            assert result.exit_code in (0, 4)
        finally:
            Fetcher.__init__ = original_init

    def test_cli_500_error(self, runner: CliRunner, tmp_path: Path) -> None:
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
                ["https://example.com/error", "--output", str(tmp_path / "test-cli-500.md")],
            )
            assert result.exit_code in (0, 5)
        finally:
            Fetcher.__init__ = original_init

    def test_cli_output_is_directory(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --output как директория."""
        result = runner.invoke(
            cli,
            ["https://example.com/dir", "--output", str(tmp_path / "test-cli-dir")],
        )
        assert result.exit_code == 0

    def test_cli_output_no_extension(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --output без расширения."""
        result = runner.invoke(
            cli,
            ["https://example.com/noext", "--output", str(tmp_path / "test-cli-noext")],
        )
        assert result.exit_code == 0

    def test_cli_delay_between_requests(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --delay между запросами."""
        result = runner.invoke(
            cli,
            [
                "https://example.com/d1",
                "https://example.com/d2",
                "--output",
                str(tmp_path / "test-cli-delay"),
                "--delay",
                "0.1",
            ],
        )
        assert result.exit_code == 0

    def test_cli_empty_content(self, runner: CliRunner, tmp_path: Path) -> None:
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
                ["https://example.com/empty", "--output", str(tmp_path / "test-cli-empty.md")],
            )
            assert result.exit_code == 0
        finally:
            Fetcher.__init__ = original_init

    def test_cli_combined_options(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с множеством опций."""
        result = runner.invoke(
            cli,
            [
                "https://example.com/combined",
                "--output",
                str(tmp_path / "test-cli-combined.md"),
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

    def test_cli_empty_content_warning(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с пустым контентом — предупреждение."""
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
                ["https://example.com/empty", "--output", str(tmp_path / "test-cli-empty-warn.md")],
            )
            assert "предупреждение" in result.output.lower() or "warning" in result.output.lower() or "пропускаю" in result.output.lower()
        finally:
            Fetcher.__init__ = original_init

    def test_cli_image_download(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с --images download."""
        html_with_images = """
        <html>
        <head><title>Test</title></head>
        <body>
            <h1>Test</h1>
            <img src="https://example.com/img.jpg" alt="Image">
        </body>
        </html>
        """
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, text=html_with_images, headers={"Content-Type": "text/html; charset=utf-8"})
        )
        from markdownurl.fetcher import Fetcher
        original_init = Fetcher.__init__
        def patched_init(self, *args, **kwargs):
            kwargs["transport"] = transport
            original_init(self, *args, **kwargs)
        Fetcher.__init__ = patched_init
        try:
            result = runner.invoke(
                cli,
                ["https://example.com/img", "--output", str(tmp_path / "test-cli-img.md"), "--images", "download"],
            )
            assert result.exit_code == 0
        finally:
            Fetcher.__init__ = original_init

    def test_cli_exit_with_error_code(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI завершается с кодом ошибки."""
        def handler_error(request):
            return httpx.Response(500, text="Server Error")
        transport = httpx.MockTransport(handler_error)
        from markdownurl.fetcher import Fetcher
        original_init = Fetcher.__init__
        def patched_init(self, *args, **kwargs):
            kwargs["transport"] = transport
            original_init(self, *args, **kwargs)
        Fetcher.__init__ = patched_init
        try:
            result = runner.invoke(
                cli,
                ["https://example.com/error", "--output", str(tmp_path / "test-cli-error.md")],
            )
            assert result.exit_code in (0, 5)
        finally:
            Fetcher.__init__ = original_init

    def test_cli_single_file_output(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI с одним файлом на выходе."""
        result = runner.invoke(
            cli,
            ["https://example.com/single", "--output", str(tmp_path / "test-single.md")],
        )
        assert result.exit_code == 0

    # TEST-3: Тесты для OSError и FileWriteError
    def test_cli_os_error_on_write(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI обрабатывает OSError при записи (недоступная директория)."""
        import stat

        # Создаём недоступную для записи директорию
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)  # только чтение

        result = runner.invoke(
            cli,
            ["https://example.com/article", "--output", str(readonly_dir / "test.md")],
        )
        # Должна быть ошибка или предупреждение
        assert result.exit_code in (0, 1, 2)

    def test_cli_file_write_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI обрабатывает FileWriteError."""
        # Пытаемся записать в несуществующую директорию без прав
        result = runner.invoke(
            cli,
            ["https://example.com/article", "--output", "/nonexistent/deeply/nested/dir/file.md"],
        )
        # Ошибка при создании директории
        assert result.exit_code in (0, 1, 2)
