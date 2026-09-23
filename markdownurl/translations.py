"""Translations for MarkdownURL CLI."""

from __future__ import annotations

import locale
import os

# --- Translations ---

TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        # CLI help text
        "cli_desc": "MarkdownURL — извлечение веб-статей в Obsidian-flavored Markdown.\n\n"
                    "Принимает один или несколько URL-адресов и сохраняет их содержимое\n"
                    "в формате Markdown, оптимизированном для Obsidian.",
        "opt_from_file": "Файл со списком URL (по одному на строку)",
        "opt_output": "Путь к выходному файлу или директории",
        "opt_no_frontmatter": "Отключить YAML-фронтматер",
        "opt_timeout": "Таймаут запроса в секундах",
        "opt_images": "Стратегия обработки изображений",
        "opt_images_dir": "Папка для скачанных изображений",
        "opt_link_format": "Формат ссылок",
        "opt_on_conflict": "Разрешение конфликтов имён файлов",
        "opt_date_prefix": "Добавить префикс даты к имени файла",
        "opt_block_ids": "Генерировать block IDs для параграфов",
        "opt_user_agent": "Переопределить User-Agent",
        "opt_delay": "Задержка между запросами в batch-режиме (сек)",
        "opt_help": "Показать справку и выйти",
        # Messages
        "err_no_urls": "Ошибка: укажите URL или файл с URL (--from-file)",
        "err_file_not_found": "Ошибка: файл не найден: {path}",
        "warn_no_content": "  Предупреждение: контент не извлечён, пропускаю",
        "warn_file_exists": "  Предупреждение: файл уже существует, пропускаю: {path}",
        "warn_generic": "  Предупреждение: {msg}",
        "err_generic": "  Ошибка: {msg}",
        "err_unexpected": "  Ошибка: непредвиденная ошибка: {msg}",
        # Progress
        "progress": "[{current}/{total}] {url}",
        "saved": "  Сохранено: {path}",
        # Summary
        "summary": "Готово: {ok} успешно, {err} ошибок, {skip} пропущено",
    },
    "en": {
        # CLI help text
        "cli_desc": "MarkdownURL — extract web articles to Obsidian-flavored Markdown.\n\n"
                    "Accepts one or more URLs and saves their content\n"
                    "as Markdown optimized for Obsidian.",
        "opt_from_file": "File with URL list (one per line)",
        "opt_output": "Output file path or directory",
        "opt_no_frontmatter": "Disable YAML frontmatter",
        "opt_timeout": "Request timeout in seconds",
        "opt_images": "Image handling strategy",
        "opt_images_dir": "Directory for downloaded images",
        "opt_link_format": "Link format",
        "opt_on_conflict": "File name conflict resolution",
        "opt_date_prefix": "Add date prefix to file name",
        "opt_block_ids": "Generate block IDs for paragraphs",
        "opt_user_agent": "Override User-Agent",
        "opt_delay": "Delay between requests in batch mode (sec)",
        "opt_help": "Show this message and exit",
        # Messages
        "err_no_urls": "Error: specify a URL or a file with URLs (--from-file)",
        "err_file_not_found": "Error: file not found: {path}",
        "warn_no_content": "  Warning: no content extracted, skipping",
        "warn_file_exists": "  Warning: file already exists, skipping: {path}",
        "warn_generic": "  Warning: {msg}",
        "err_generic": "  Error: {msg}",
        "err_unexpected": "  Error: unexpected error: {msg}",
        # Progress
        "progress": "[{current}/{total}] {url}",
        "saved": "  Saved: {path}",
        # Summary
        "summary": "Done: {ok} OK, {err} errors, {skip} skipped",
    },
}


def _get_locale() -> str:
    """Detect system locale. Returns 'ru' or 'en'."""
    # Check LANG/LC_ALL environment variables
    lang = os.environ.get("LANG", "")
    lc_all = os.environ.get("LC_ALL", "")
    lc_ctype = os.environ.get("LC_CTYPE", "")

    for var in (lc_all, lc_ctype, lang):
        if var.lower().startswith("ru"):
            return "ru"

    # Fallback to locale module
    try:
        loc = locale.getlocale(locale.LC_MESSAGES)
        if loc and loc[0] and loc[0].lower().startswith("ru"):
            return "ru"
    except (ValueError, TypeError):
        pass

    # Fallback to getdefaultlocale
    try:
        dfl = locale.getdefaultlocale()
        if dfl and dfl[0] and dfl[0].lower().startswith("ru"):
            return "ru"
    except (ValueError, TypeError):
        pass

    return "en"


LOCALE = _get_locale()
T = TRANSLATIONS[LOCALE]


def t(key: str, **kwargs: str) -> str:
    """Translate a key, optionally formatting with kwargs.

    Args:
        key: Ключ перевода.
        **kwargs: Аргументы для форматирования строки.

    Returns:
        Переведённая строка с подставленными аргументами.
    """
    msg = T.get(key, key)
    if kwargs:
        try:
            msg = msg.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            # Если аргументы не соответствуют шаблону, возвращаем без форматирования
            pass
    return msg
