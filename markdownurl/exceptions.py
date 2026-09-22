"""Кастомные исключения для MarkdownURL."""

from __future__ import annotations


class MarkdownURLError(Exception):
    """Базовое исключение пакета."""


class FetchError(MarkdownURLError):
    """Ошибка загрузки страницы."""

    def __init__(self, url: str, message: str, status_code: int | None = None) -> None:
        self.url = url
        self.status_code = status_code
        full_message = f"{message}"
        if status_code:
            full_message = f"{message} (HTTP {status_code})"
        super().__init__(full_message)


class FetchTimeoutError(MarkdownURLError):
    """Таймаут запроса."""

    def __init__(self, url: str, timeout: float) -> None:
        self.url = url
        self.timeout = timeout
        super().__init__(f"Таймаут запроса ({timeout} сек): {url}")


class ExtractionError(MarkdownURLError):
    """Ошибка извлечения контента."""

    def __init__(self, url: str, message: str = "Контент не извлечён") -> None:
        self.url = url
        super().__init__(f"{message}: {url}")


class FileWriteError(MarkdownURLError):
    """Ошибка записи файла."""

    def __init__(self, path: str, message: str = "Не удалось записать файл") -> None:
        self.path = path
        super().__init__(f"{message}: {path}")


class ImageDownloadError(MarkdownURLError):
    """Ошибка скачивания изображения."""

    def __init__(self, url: str, message: str = "Не удалось скачать изображение") -> None:
        self.url = url
        super().__init__(f"{message}: {url}")
