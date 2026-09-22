"""MarkdownURL — извлечение веб-статей в Obsidian-flavored Markdown."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from markdownurl.converter import Converter
from markdownurl.exceptions import (
    ExtractionError,
    FetchError,
    FileWriteError,
    ImageDownloadError,
    MarkdownURLError,
    TimeoutError,
)
from markdownurl.extractor import ArticleMetadata, Extractor, ImageInfo
from markdownurl.fetcher import Fetcher
from markdownurl.frontmatter import FrontmatterGenerator
from markdownurl.images import ImageProcessor
from markdownurl.namer import Namer


@dataclass
class ArticleResult:
    """Результат извлечения статьи."""

    url: str
    title: str
    markdown: str
    frontmatter: dict
    frontmatter_yaml: str = ""
    filepath: Path | None = None
    status: str = "success"  # success, error, skip

    @property
    def success(self) -> bool:
        """True если статья успешно извлечена и сохранена."""
        return self.status == "success"

    def save(self, path: str | Path | None = None) -> Path:
        """Сохранить статью в файл.

        Args:
            path: Путь к файлу. Если None — используется self.filepath.

        Returns:
            Путь к сохранённому файлу.
        """
        if path is None and self.filepath is None:
            raise ValueError("Не указан путь для сохранения")

        target = Path(path) if path else self.filepath
        if target is None:
            raise ValueError("Не указан путь для сохранения")

        target.parent.mkdir(parents=True, exist_ok=True)
        full_content = self.frontmatter_to_yaml() + "\n\n" + self.markdown
        target.write_text(full_content, encoding="utf-8")
        return target

    def frontmatter_to_yaml(self) -> str:
        """Сериализовать фронтматер в YAML-строку."""
        if self.frontmatter_yaml:
            return self.frontmatter_yaml
        gen = FrontmatterGenerator()
        # Создаём временный ArticleMetadata из dict
        meta = ArticleMetadata(
            title=self.frontmatter.get("title", ""),
            author=self.frontmatter.get("author", ""),
            date=self.frontmatter.get("date", ""),
            description=self.frontmatter.get("description", ""),
            tags=self.frontmatter.get("tags", []),
            og_title=self.frontmatter.get("og_title", ""),
        )
        return gen.generate(meta, self.frontmatter.get("source", self.url))


def fetch_article(
    url: str,
    output: str | Path | None = None,
    include_frontmatter: bool = True,
    timeout: float = 10.0,
    images: str = "link",
    images_dir: str = "attachments",
    link_format: str = "wikilink",
    conflict: str = "suffix",
    date_prefix: bool = False,
    block_ids: bool = False,
    user_agent: str | None = None,
) -> ArticleResult:
    """Извлечь статью по URL и сохранить в Markdown.

    Args:
        url: URL-адрес статьи.
        output: Путь к выходному файлу. Если None — генерируется автоматически.
        include_frontmatter: Включить YAML-фронтматер.
        timeout: Таймаут запроса в секундах.
        images: Стратегия обработки изображений (link/download/skip).
        images_dir: Папка для скачанных изображений.
        link_format: Формат ссылок (wikilink/markdown).
        conflict: Разрешение конфликтов (suffix/overwrite/skip).
        date_prefix: Добавить префикс даты к имени файла.
        block_ids: Генерировать block IDs для параграфов.
        user_agent: Переопределить User-Agent.

    Returns:
        ArticleResult с markdown-контентом и метаданными.
    """
    output_path: Path | None = Path(output) if output else None
    output_dir = output_path.parent if output_path and output_path.parent != Path(".") else Path(".")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Инициализируем компоненты
    fetcher = Fetcher(timeout=timeout, user_agent=user_agent)
    extractor = Extractor()
    converter = Converter()
    frontmatter_gen = FrontmatterGenerator()
    namer = Namer(date_prefix=date_prefix, on_conflict=conflict)
    image_proc = ImageProcessor(
        output_dir=output_dir,
        namer=namer,
        images_dir=images_dir,
        timeout=timeout,
    )

    try:
        # Загрузка
        html, encoding = fetcher.fetch_and_decode(url)

        # Извлечение
        md_content, meta, img_infos = extractor.extract(html, url)

        if not md_content.strip():
            raise ExtractionError(url, "Контент не извлечён")

        # Обработка изображений
        if images == "download" and img_infos:
            md_content = image_proc.process_images(md_content, url, img_infos)

        # Конвертация
        md_content = converter.convert(
            md_content,
            url=url,
            link_format=link_format,
            block_ids=block_ids,
        )

        # Фронтматер
        fm_dict = frontmatter_gen.to_dict(meta, url)
        fm_str = frontmatter_gen.generate(meta, url, include_frontmatter=include_frontmatter)

        # Имя файла
        if output_path:
            filepath = output_path
            if not filepath.suffix:
                filepath = filepath.with_suffix(".md")
        else:
            name = namer.generate_name(
                meta.title or "untitled",
                url=url,
                date_str=meta.date,
            )
            filepath = output_dir / name

        # Разрешение конфликтов
        resolved_path, action = namer.resolve_conflict(filepath)
        if action == "skip":
            return ArticleResult(
                url=url,
                title=meta.title or "Untitled",
                markdown=md_content,
                frontmatter=fm_dict,
                frontmatter_yaml=fm_str,
                filepath=None,
                status="skip",
            )

        # Запись
        full_content = fm_str + "\n\n" + md_content if fm_str else md_content
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(full_content, encoding="utf-8")

        return ArticleResult(
            url=url,
            title=meta.title or "Untitled",
            markdown=md_content,
            frontmatter=fm_dict,
            frontmatter_yaml=fm_str,
            filepath=resolved_path,
            status="success",
        )

    except FetchError:
        return ArticleResult(
            url=url,
            title="",
            markdown="",
            frontmatter={},
            status="error",
        )
    except ExtractionError:
        return ArticleResult(
            url=url,
            title="",
            markdown="",
            frontmatter={},
            status="skip",
        )


def fetch_articles(
    urls: list[str],
    output_dir: str | Path = ".",
    delay: float = 0.0,
    **kwargs,
) -> list[ArticleResult]:
    """Пакетное извлечение статей.

    Args:
        urls: Список URL-адресов.
        output_dir: Директория для сохранения файлов.
        delay: Задержка между запросами в секундах.
        **kwargs: Дополнительные аргументы для fetch_article.

    Returns:
        Список ArticleResult.
    """
    results: list[ArticleResult] = []

    for i, url in enumerate(urls):
        result = fetch_article(url, **kwargs)
        results.append(result)

        if delay > 0 and i < len(urls) - 1:
            time.sleep(delay)

    return results


__all__ = [
    "fetch_article",
    "fetch_articles",
    "ArticleResult",
    "MarkdownURLError",
    "FetchError",
    "ExtractionError",
    "FileWriteError",
    "ImageDownloadError",
    "TimeoutError",
    "ArticleMetadata",
    "ImageInfo",
]
