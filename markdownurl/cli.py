"""CLI-интерфейс MarkdownURL."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import click

from markdownurl.converter import Converter
from markdownurl.exceptions import (
    ExtractionError,
    FetchError,
    FileWriteError,
    MarkdownURLError,
    TimeoutError,
)
from markdownurl.extractor import Extractor
from markdownurl.fetcher import Fetcher
from markdownurl.frontmatter import FrontmatterGenerator
from markdownurl.images import ImageProcessor
from markdownurl.namer import Namer
from markdownurl.translations import t


IMAGE_MODES = click.Choice(["link", "download", "skip"], case_sensitive=False)
LINK_FORMATS = click.Choice(["wikilink", "markdown"], case_sensitive=False)
CONFLICT_MODES = click.Choice(["suffix", "overwrite", "skip"], case_sensitive=False)


def _read_urls_file(filepath: str) -> list[str]:
    """Прочитать список URL из файла (по одному на строку)."""
    path = Path(filepath)
    if not path.exists():
        click.echo(t("err_file_not_found", path=filepath), err=True)
        sys.exit(2)
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


@click.command(context_settings={"max_content_width": 80})
@click.argument("urls", nargs=-1, required=False)
@click.option(
    "--from-file",
    "urls_file",
    type=str,
    default=None,
    help=t("opt_from_file"),
)
@click.option(
    "--output",
    type=str,
    default=None,
    help=t("opt_output"),
)
@click.option(
    "--no-frontmatter",
    is_flag=True,
    default=False,
    help=t("opt_no_frontmatter"),
)
@click.option(
    "--timeout",
    type=float,
    default=10.0,
    help=t("opt_timeout"),
)
@click.option(
    "--images",
    type=IMAGE_MODES,
    default="link",
    help=t("opt_images"),
)
@click.option(
    "--images-dir",
    type=str,
    default="attachments",
    help=t("opt_images_dir"),
)
@click.option(
    "--format",
    type=LINK_FORMATS,
    default="wikilink",
    help=t("opt_link_format"),
)
@click.option(
    "--conflict",
    type=CONFLICT_MODES,
    default="suffix",
    help=t("opt_on_conflict"),
)
@click.option(
    "--date-prefix",
    is_flag=True,
    default=False,
    help=t("opt_date_prefix"),
)
@click.option(
    "--block-ids",
    is_flag=True,
    default=False,
    help=t("opt_block_ids"),
)
@click.option(
    "--user-agent",
    type=str,
    default=None,
    help=t("opt_user_agent"),
)
@click.option(
    "--delay",
    type=float,
    default=0.0,
    help=t("opt_delay"),
)
def cli(
    urls: tuple[str, ...],
    urls_file: str | None,
    output: str | None,
    no_frontmatter: bool,
    timeout: float,
    images: str,
    images_dir: str,
    format: str,
    conflict: str,
    date_prefix: bool,
    block_ids: bool,
    user_agent: str | None,
    delay: float,
) -> None:
    """MarkdownURL — extract web articles to Obsidian-flavored Markdown."""
    url_list: list[str] = list(urls)

    if urls_file:
        file_urls = _read_urls_file(urls_file)
        url_list.extend(file_urls)

    if not url_list:
        click.echo(t("err_no_urls"), err=True)
        sys.exit(2)

    output_dir: Path
    if output:
        out_path = Path(output)
        output_dir = out_path if out_path.is_dir() else (out_path.parent if out_path.parent != Path(".") else Path("."))
    else:
        output_dir = Path(".")

    output_dir.mkdir(parents=True, exist_ok=True)

    fetcher = Fetcher(timeout=timeout, user_agent=user_agent)
    extractor = Extractor()
    converter = Converter()
    frontmatter_gen = FrontmatterGenerator()
    namer = Namer(date_prefix=date_prefix, on_conflict=conflict)
    image_proc = ImageProcessor(output_dir=output_dir, namer=namer, images_dir=images_dir, timeout=timeout)

    success_count = 0
    error_count = 0
    skip_count = 0
    last_error_code: int = 0

    for i, url in enumerate(url_list):
        click.echo(t("progress", current=i + 1, total=len(url_list), url=url), err=True)

        try:
            html, encoding = fetcher.fetch_and_decode(url)
            md_content, meta, img_infos = extractor.extract(html, url)

            if not md_content.strip():
                click.echo(t("warn_no_content"), err=True)
                skip_count += 1
                continue

            if images == "download" and img_infos:
                md_content = image_proc.process_images(md_content, url, img_infos)

            md_content = converter.convert(md_content, url=url, link_format=format, block_ids=block_ids)
            fm = frontmatter_gen.generate(meta, url, include_frontmatter=not no_frontmatter)

            if output and not Path(output).is_dir() and i == 0 and len(url_list) == 1:
                filepath = Path(output)
                if not filepath.suffix:
                    filepath = filepath.with_suffix(".md")
            else:
                name = namer.generate_name(meta.title or "untitled", url=url, date_str=meta.date)
                filepath = output_dir / name

            resolved_path, action = namer.resolve_conflict(filepath)
            if action == "skip":
                click.echo(t("warn_file_exists", path=resolved_path), err=True)
                skip_count += 1
                continue

            full_content = fm + "\n\n" + md_content if fm else md_content
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_path.write_text(full_content, encoding="utf-8")

            click.echo(t("saved", path=resolved_path), err=True)
            success_count += 1

        except FetchError as exc:
            if hasattr(exc, "status_code") and exc.status_code == 404:
                click.echo(t("warn_generic", msg=exc), err=True)
                skip_count += 1
                last_error_code = 4
            elif hasattr(exc, "status_code") and exc.status_code and exc.status_code >= 500:
                click.echo(t("warn_generic", msg=exc), err=True)
                error_count += 1
                last_error_code = 5
            else:
                click.echo(t("warn_generic", msg=exc), err=True)
                error_count += 1
                last_error_code = 2

        except TimeoutError as exc:
            click.echo(t("warn_generic", msg=exc), err=True)
            error_count += 1
            last_error_code = 3

        except ExtractionError as exc:
            click.echo(t("warn_generic", msg=exc), err=True)
            skip_count += 1
            last_error_code = 6

        except FileWriteError as exc:
            click.echo(t("err_generic", msg=exc), err=True)
            error_count += 1
            last_error_code = 7

        except MarkdownURLError as exc:
            click.echo(t("err_generic", msg=exc), err=True)
            error_count += 1
            last_error_code = 1

        except OSError as exc:
            click.echo(t("err_unexpected", msg=exc), err=True)
            error_count += 1
            last_error_code = 1

        if i < len(url_list) - 1 and delay > 0:
            time.sleep(delay)

    click.echo("", err=True)
    click.echo(t("summary", ok=success_count, err=error_count, skip=skip_count), err=True)

    if last_error_code != 0:
        sys.exit(last_error_code)


if __name__ == "__main__":
    cli()
