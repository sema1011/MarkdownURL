"""Генерация имён файлов: слагификация, обрезка, префикс даты, конфликты."""

from __future__ import annotations

import hashlib
import re
from html import unescape
from pathlib import Path


class Namer:
    """Генерация именов файлов для MarkdownURL."""

    MAX_LENGTH = 80
    TRUNCATION_SUFFIX = "…"

    # Запрещённые символы на всех платформах
    FORBIDDEN_ALL = re.compile(r'[\[\]\#\^|]')
    # Запрещённые символы на Windows/macOS
    FORBIDDEN_WIN_MAC = re.compile(r'[\\/:*?"<>]')
    # Все запрещённые в одном паттерне
    FORBIDDEN = re.compile(r'[\[\]\#\^\|\\/:*?"<>¶]')

    def __init__(
        self,
        date_prefix: bool = False,
        on_conflict: str = "suffix",
    ) -> None:
        self.date_prefix = date_prefix
        self.on_conflict = on_conflict

    def generate_name(
        self,
        title: str,
        url: str = "",
        date_str: str = "",
    ) -> str:
        """Сгенерировать имя файла из заголовка статьи.

        Args:
            title: Заголовок статьи.
            url: URL (для уникальности при обрезке).
            date_str: Дата в формате YYYY-MM-DD (для префикса).

        Returns:
            Имя файла с расширением .md.
        """
        slug = self.slugify(title)

        if self.date_prefix and date_str:
            slug = f"{date_str}-{slug}"

        # Обрезка
        slug = self._truncate(slug, url)

        return f"{slug}.md"

    def slugify(self, text: str) -> str:
        """Конвертировать текст в слаг.

        1. Убираем HTML-теги.
        2. Удаляем запрещённые символы.
        3. Заменяем пробелы на -.
        4. Убираем множественные -.
        5. Убираем - на концах.
        """
        # Убираем HTML-теги
        text = re.sub(r'<[^>]+>', '', text)
        # Убираем HTML-сущности
        text = unescape(text)
        # Удаляем запрещённые символы
        text = self.FORBIDDEN.sub('', text)
        # Убираем любые не-буквенно-цифренные символы (кроме пробелов, дефисов, подчёркиваний)
        # Это убирает ¶, §, ©, ™, ®, и другие Unicode-спецсимволы
        text = re.sub(r'[^\w\s\-_]', '', text, flags=re.UNICODE)
        # Заменяем пробелы и _ на -
        text = re.sub(r'[\s_]+', '-', text)
        # Убираем множественные дефисы
        text = re.sub(r'-{2,}', '-', text)
        # Убираем дефисы на концах
        text = text.strip('-')
        # Приводим к нижнему регистру
        text = text.lower()

        return text

    def _truncate(self, slug: str, url: str = "") -> str:
        """Обрезать слаг до MAX_LENGTH символов."""
        if len(slug) <= self.MAX_LENGTH:
            return slug

        # Если slug уже длинный, обрезаем и добавляем хэш URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:6] if url else ""

        truncated = slug[: self.MAX_LENGTH - len(self.TRUNCATION_SUFFIX) - (7 if url_hash else 1)]
        result = truncated.rstrip('-') + self.TRUNCATION_SUFFIX
        if url_hash:
            result += f"-{url_hash}"

        return result

    def resolve_conflict(self, filepath: Path) -> tuple[Path, str]:
        """Разрешить конфликт имён файлов.

        Args:
            filepath: Желаемый путь к файлу.

        Returns:
            Кортеж (новый_путь, действие).
            действие: 'new', 'overwrite', 'skip', или 'suffixed'.
        """
        if not filepath.exists():
            return filepath, "new"

        if self.on_conflict == "overwrite":
            return filepath, "overwrite"

        if self.on_conflict == "skip":
            return filepath, "skip"

        # suffix — добавляем числовой суффикс
        stem = filepath.stem
        suffix = filepath.suffix
        parent = filepath.parent

        counter = 2
        while True:
            new_name = f"{stem}-{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path, "suffixed"
            counter += 1

    def resolve_conflict_download(
        self,
        filename: str,
        existing_names: set[str],
    ) -> str:
        """Разрешить конфликт для имени файла изображений.

        Args:
            filename: Желаемое имя файла.
            existing_names: Множество уже существующих имён.

        Returns:
            Уникальное имя файла.
        """
        if filename not in existing_names:
            return filename

        if self.on_conflict == "overwrite":
            return filename

        if self.on_conflict == "skip":
            return ""  # Пустое имя = пропуск

        # suffix
        stem, ext = self._split_stem_ext(filename)
        counter = 2
        while True:
            new_name = f"{stem}-{counter}{ext}"
            if new_name not in existing_names:
                return new_name
            counter += 1

    @staticmethod
    def _split_stem_ext(filename: str) -> tuple[str, str]:
        """Разделить имя файла на stem и extension."""
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            return parts[0], f".{parts[1]}"
        return parts[0], ""
