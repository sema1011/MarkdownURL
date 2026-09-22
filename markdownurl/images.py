"""Скачивание и обработка изображений."""

from __future__ import annotations

import re
from hashlib import md5
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import httpx

from markdownurl.extractor import ImageInfo
from markdownurl.namer import Namer

# Расширения, которые считаем изображениями
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".avif",
}


class ImageProcessor:
    """Скачивание и обработка изображений для Obsidian."""

    def __init__(
        self,
        output_dir: Path,
        namer: Namer,
        images_dir: str = "attachments",
        timeout: float = 10.0,
    ) -> None:
        self.output_dir = output_dir
        self.namer = namer
        self.images_dir = images_dir
        self.timeout = timeout
        self._existing_names: set[str] = set()

    def process_images(
        self,
        markdown: str,
        base_url: str,
        images: list[ImageInfo],
    ) -> str:
        """Скачать изображения и заменить ссылки в Markdown на Obsidian-эмбеды.

        Args:
            markdown: Markdown-контент с ссылками на изображения.
            base_url: Базовый URL для относительных ссылок.
            images: Список ImageInfo из extractor.

        Returns:
            Markdown с заменёнными ссылками на эмбеды.
        """
        if not images:
            return markdown

        self._existing_names = set()
        # Находим уже существующие файлы в images_dir/
        attachments_dir = self.output_dir / self.images_dir
        if attachments_dir.exists():
            for f in attachments_dir.iterdir():
                if f.is_file():
                    self._existing_names.add(f.name)

        # Собираем mapping: src -> (saved_filename, width)
        replacements: dict[str, tuple[str, int | None]] = {}

        for img in images:
            src = img.src.strip()
            if not src:
                continue

            # Пропускаем data: URLs и относительные без base
            if src.startswith("data:") or src.startswith("//"):
                continue

            # Конвертируем относительные в абсолютные
            if not src.startswith("http://") and not src.startswith("https://"):
                src = urljoin(base_url, src)

            # Скачиваем
            filename = self._download_image(src, img.alt)
            if filename:
                width = img.width if img.width and img.width > 0 else None
                replacements[src] = (filename, width)

        # Заменяем ссылки в Markdown
        markdown = self._replace_image_links(markdown, replacements)

        return markdown

    def _download_image(self, url: str, alt: str = "") -> str | None:
        """Скачать изображение в attachments/.

        Returns:
            Имя файла или None при ошибке.
        """
        attachments_dir = self.output_dir / self.images_dir
        attachments_dir.mkdir(parents=True, exist_ok=True)

        # Генерируем имя файла
        filename = self._generate_filename(url, alt)
        if not filename:
            return None

        # Разрешаем конфликт
        filename = self.namer.resolve_conflict_download(
            filename, self._existing_names
        )
        if not filename:
            return None  # skip

        filepath = attachments_dir / filename
        self._existing_names.add(filename)

        try:
            with httpx.Client() as client:
                response = client.get(url, timeout=self.timeout)
                response.raise_for_status()

                # Проверяем, что это изображение
                content_type = response.headers.get("content-type", "")
                if "image/" not in content_type:
                    # Пробуем определить по расширению URL
                    url_ext = self._extract_extension(url)
                    if url_ext and url_ext.lower() in IMAGE_EXTENSIONS:
                        pass  # OK
                    else:
                        return None

                filepath.write_bytes(response.content)
                return filename

        except (httpx.HTTPError, OSError):
            # Ошибка скачивания — оставляем исходную ссылку
            return None

    def _generate_filename(self, url: str, alt: str = "") -> str:
        """Сгенерировать имя файла для изображения.

        Формат: {slug}_{index}.{ext}
        """
        # Определяем расширение из URL
        parsed = urlparse(url)
        path = unquote(parsed.path)
        ext = self._extract_extension(path)

        if not ext or ext.lower() not in IMAGE_EXTENSIONS:
            ext = ".jpg"  # fallback

        # Генерируем slug из alt или URL
        if alt and alt.strip():
            slug = self.namer.slugify(alt.strip())
        else:
            # Хэш URL
            slug = md5(url.encode()).hexdigest()[:8]

        return f"{slug}{ext}"

    @staticmethod
    def _extract_extension(path: str) -> str:
        """Извлечь расширение из пути."""
        # Убираем query string
        path = path.split("?")[0].split("#")[0]
        return Path(path).suffix.lower()

    def _replace_image_links(self, markdown: str, replacements: dict) -> str:
        """Заменить ссылки на изображения в Markdown на Obsidian-эмбеды."""
        def _replace(match: re.Match) -> str:
            url = match.group(3) or match.group(2)

            if url in replacements:
                filename, width = replacements[url]
                if width:
                    return f"![[{filename}|{width}]]"
                return f"![[{filename}]]"

            return match.group(0)

        # Обрабатываем стандартные ссылки ![alt](url)
        markdown = re.sub(
            r'(!?)\[(.*?)\]\(([^)]+)\)',
            _replace,
            markdown,
        )

        # Обрабатываем HTML <img> теги, которые могли остаться
        def _replace_html_img(match: re.Match) -> str:
            src = match.group(1) or ""

            if src in replacements:
                filename, width = replacements[src]
                if width:
                    return f"![[{filename}|{width}]]"
                return f"![[{filename}]]"

            # Оставляем как есть с комментарием
            return f"<!-- image download failed: {src} -->"

        markdown = re.sub(
            r'<img[^>]*src\s*=\s*["\']([^"\']*)["\'][^>]*(?:alt\s*=\s*["\']([^"\']*)["\'])?[^>]*>',
            _replace_html_img,
            markdown,
            flags=re.IGNORECASE,
        )

        # Fallback: img с width
        markdown = re.sub(
            r'<img[^>]*src\s*=\s*["\']([^"\']*)["\'][^>]*(?:alt\s*=\s*["\']([^"\']*)["\'])?[^>]*width\s*=\s*["\'](\d+)["\'][^>]*>',
            _replace_html_img,
            markdown,
            flags=re.IGNORECASE,
        )

        return markdown
