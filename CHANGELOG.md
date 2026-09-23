# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.4] - 2026-09-23

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
