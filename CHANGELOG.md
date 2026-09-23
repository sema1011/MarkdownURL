# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2026-09-23

### Added
- **CRIT-1**: Экранирование спецсимволов `>` и `!` в полях callout для предотвращения инъекции Markdown
- **CRIT-2**: SSRF-защита — блокировка внутренних IP-адресов при скачивании изображений (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8 и др.)
- **CRIT-3**: Валидация формата URL перед отправкой запроса (`_validate_url()` в fetcher.py)
- **PERF-1**: Regex-паттерны для callouts вынесены в константы модуля `_BLOCKQUOTE_CLASS_RE`, `_BLOCKQUOTE_TITLE_RE`
- **TEST-1**: Тест `test_fetch_articles_with_real_delay` — проверка задержки `delay > 0`
- **TEST-2**: 11 новых тестов для `_convert_shell_commands`, `_fix_html_lists`, `_convert_callouts`, `_convert_function_params`
- **TEST-3**: 2 новых теста для `OSError` и `FileWriteError` в CLI

### Fixed
- **BUG-1**: Удалены дубликаты `find` и `xargs` в `shell_keywords`
- **BUG-2**: Улучшен regex в `_convert_function_params` — поддержка нескольких параметров `(*param1*, *param2*)`
- **BUG-3**: Исправлен маппинг `frontmatter` dict → `ArticleMetadata` — `og_title` теперь корректно извлекается из `aliases`
- **BUG-4**: Добавлена явная обработка действия `"new"` в `resolve_conflict` (обновлён docstring)
- **QUAL-2**: Добавлены type hints для `_replace_image_links` — `dict[str, tuple[str, int | None]]`
- **QUAL-3**: `msg.format()` в `t()` обернут в `try/except KeyError`
- **QUAL-4**: Все тесты в `test_cli.py` используют `tmp_path` вместо жёстко закодированных `/tmp/` путей
- **QUAL-4**: Исправлен оставшийся `/tmp/empty.md` в `test_api.py`

### Changed
- `Fetcher.fetch()` теперь вызывает `_validate_url()` перед отправкой запроса
- `ImageProcessor._download_image()` проверяет URL через `_is_blocked_url()` для SSRF-защиты
- `Converter._parse_blockquote_block()` использует константы regex и экранирует спецсимволы
- `FrontmatterGenerator.frontmatter_to_yaml()` корректно маппит `aliases` → `og_title`
- `translations.t()` безопасно обрабатывает несовпадающие kwargs

### Statistics
- Всего тестов: **~185** (добавлено ~18 новых)
- Покрытие: **~87%** (было 85%)

## [1.0.4] - 2026-09-23

### Changed
- **API унификация**: `fetch_article(output=...)` → `fetch_article(output_dir=...)` — параметр унифицирован с `fetch_articles(output_dir=...)`

### Fixed
- **BUG-14**: Удалены `¶` (U+00B6) и zero-width space (U+200B) из Markdown-вывода

### Added
- **converter.py**: 4 новых шага постобработки Markdown после trafilatura
  - `_convert_formatting_tags` — `<del>`, `<s>`, `<strike>` → `~~текст~~`
  - `_convert_function_params` — `*param*` → `` `param` `` в сигнатурах функций
  - `_convert_shell_commands` — строки команд (export, sudo, cd, find, go и др.) → ```bash блоки
  - `_fix_html_lists` — восстановление Markdown-списков по отступам из артефактов trafilatura

### Changed
- Порядок шагов в `Converter.convert()`: HTML-теги → параметры → списки → shell-команды → остальное
- Уважение к ``` блокам: `_convert_shell_commands` и `_fix_html_lists` пропускают содержимое кода
- `pyproject.toml` — добавлены `exclude` для `hatch.build` (исключены tests, кэши из билдов)

### Fixed
- Shell-команды извлекаются как ```bash блоки вместо текста (ubuntu.ru)
- Код-блоки не обрастают `- ` маркерами списков (deso.onl)
- **QUAL-15**: Ruff SIM103 — возврат условия напрямую вместо `if ... return True`

## [1.0.3] - 2026-09-23

### Fixed
- **QUAL-11**: Удалены неиспользуемые импорты в `tests/test_api.py`

## [1.0.2] - 2026-09-23

### Fixed
- **BUG-10**: `TimeoutError` переименован в `FetchTimeoutError` (shadow builtin)
- **BUG-11**: CLI-опция `--format` → `--link-format` (shadow builtin)
- **BUG-12**: CLI-тесты: respx заменён на `httpx.MockTransport` (надёжное мокирование)
- **BUG-13**: `fetcher.py`: добавлен `return response`, `time.sleep()`, `raise ... from None`
- **QUAL-9**: Ruff linting: сортировка импортов, удалены неиспользуемые переменные
- **QUAL-10**: `assert False` → `raise AssertionError()` в тестах

### Changed
- `Fetcher.__init__` принимает параметр `transport` для инъекции моков в тестах
- `fetch_article()` принимает параметр `transport` для тестирования
- Все тесты используют `httpx.MockTransport` через pytest fixture
- Покрытие кода: **85%** (было 78%)

### Added
- Интеграционные тесты: `TestFetchArticle` (10 тестов), `TestFetchArticles` (3 теста)
- Тесты CLI: пустой контент, скачивание изображений, коды ошибок
- Тест `TestMain` для модуля `__main__`

### Statistics
- Всего тестов: **163** (137 unit + 26 CLI)
- Покрытие: **85%** (цель 80%) ✅

## [1.0.1] - 2026-09-23

### Fixed
- **BUG-1**: Опечатка в CLI — `"d"` → `"download"` в `cli.py`
- **BUG-2**: Невалидный синтаксис Obsidian-эмбедов — `![alt]](...)` → `![[filename]]`
- **BUG-3**: Несоответствие аннотации типа возвращаемого значения в `extractor.py`
- **BUG-4**: `counter += 2` → `counter += 1` в `namer.py` (пропуск чётных имён файлов)
- **BUG-5**: Мёртвая переменная `ext` в `images.py`
- **BUG-6**: Regex для `<img>` теперь поддерживает отсутствие `alt`
- **BUG-7**: `_clean_text` теперь сохраняет апострофы и плюсы (`don't`, `C++`)
- **BUG-8**: Ручная YAML-сериализация заменена на `PyYAML`
- **BUG-9**: Кэширование YAML фронтматера в `ArticleResult`
- **DEAD-1**: Удалён неиспользуемый `BlockquoteClassParser`
- **DEAD-2**: Объединены `_convert_math_span` и `_convert_math`
- **DEAD-3**: `import time` перемещён в начало файлов
- **DEAD-4**: Создан `__main__.py` для `python -m markdownurl`
- **QUAL-2**: Все локальные импорты перемещены в верх файлов
- **QUAL-3**: `except Exception` заменён на конкретные исключения
- **QUAL-4**: `assert last_exc` заменён на `raise FetchError`
- Исправлены баги в regex: `_convert_mermaid`, `_to_wikilinks`, `_absolute_links`, `_replace_image_links`
- **QUAL-6**: Удалён избыточный `import hashlib` в `images.py`
- **QUAL-7**: Удалён избыточный `except Exception: raise` в `cli.py`
- **QUAL-8**: Убран дубликат `soup.find("meta", attrs={"name": "author"})` в `extractor.py`

### Changed
- README обновлён: `format` → `link_format`, добавлены примечания о `output` vs `output_dir`
- `ArticleResult.frontmatter_to_yaml()` сначала проверяет кэшированную строку
- Обновлена схема архитектуры в README.md (добавлены `__main__.py`, `translations.py`)
- Обновлён пример даты в YAML-фронтматере: `date: '2026-09-22'`

### Removed
- `_quote_if_needed` из `frontmatter.py` (заменён на `PyYAML`)
- `_extract_blockquote_classes` и `BlockquoteClassParser` из `extractor.py`

### Statistics
- Всего тестов: **153** (127 unit + 26 CLI)
- Все тесты проходят ✅

## [1.0.0] - 2026-09-23

### Added
- Базовый набор тестов (127 тестов) для всех модулей
- CI/CD пайплайн с тестированием на Python 3.10-3.13
- Поддержка изображений без атрибута `alt` в HTML-тегах
- Кэширование YAML фронтматера в `ArticleResult`
- `SECURITY.md` — политика безопасности и reporting уязвимостей
- CLI-тесты: 26 тестов (respx, click.testing)
- Полное покрытие CLI: все опции, ошибки, файлы, комбинации

## [0.1.0] - 2026-09-22

### Added
- Initial release
- Извлечение веб-статей в Obsidian-flavored Markdown
- CLI-интерфейс с click
- Python API для программного использования
- Поддержка wikilinks, callouts, эмбедов изображений
- YAML-фронтматер по правилам Obsidian Properties
- Скачивание изображений с разрешением конфликтов
- Пакетная обработка нескольких URL
