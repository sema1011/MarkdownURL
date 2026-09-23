# MarkdownURL

Извлечение веб-статей из интернета и сохранение в формате **Obsidian Flavored Markdown** — с YAML-фронтматтером, wikilinks, callouts, эмбедами изображений и другими расширениями синтаксиса Obsidian.

Работает **снаружи** Obsidian — из терминала, скрипта, cron или CI/CD-пайплайна. Не требует запущенного Obsidian.

## Возможности

- **Извлечение контента** — автоматическое определение основного текста статьи, удаление рекламы, навигации и прочего шума.
- **Obsidian Flavored Markdown** — wikilinks, callouts (`> [!info]`), эмбеды изображений (`![[image.png]]`), выделение (`==текст==`), комментарии (`%%текст%%`).
- **YAML-фронтматтер** — свойства Obsidian (`title`, `author`, `date`, `tags`, `source` и др.).
- **Скачивание изображений** — локальное сохранение в папку `attachments/` с эмбедами.
- **Пакетная обработка** — несколько URL из аргументов или файла.
- **Гибкая настройка** — форматы ссылок, обработка конфликтов, префикс даты, block IDs.

## Установка

Создайте и активируйте виртуальное окружение:

```bash
python -m venv .venv
source .venv/bin/activate
```

Затем установите пакет из исходного кода:

```bash
pip install -e .
```

> [!note]
> Пакет не публикуется на PyPI. Предназначен для локального использования.

## Использование

### CLI

#### Одиночная статья

```bash
# Базовое использование
markdownurl https://example.com/article

# Сохранить в конкретный файл
markdownurl https://example.com/article --output notes/my-article.md

# Скачивание изображений в attachments/
markdownurl https://example.com/article --images download

# Стандартный Markdown (без wikilinks)
markdownurl https://example.com/article --link-format markdown

# Без фронтматтера
markdownurl https://example.com/article --no-frontmatter
```

#### Пакетная обработка

```bash
# Несколько URL
markdownurl https://site1.com/article https://site2.com/article -o notes/

# Из файла (по одному URL на строку)
markdownurl --from-file urls.txt -o notes/ --delay 2
```

#### Полная справка

```bash
markdownurl --help
```

| Флаг | Описание | По умолчанию |
|------|-----------|:---:|
| `--output` | Путь к файлу или директории | Текущая папка |
| `--from-file` | Файл со списком URL | — |
| `--no-frontmatter` | Отключить YAML-фронтматтер | Включён |
| `--timeout` | Таймаут запроса (сек) | `10` |
| `--images` | `link` / `download` / `skip` | `link` |
| `--images-dir` | Папка для скачанных изображений | `attachments` |
| `--link-format` | `wikilink` / `markdown` | `wikilink` |
| `--conflict` | `suffix` / `overwrite` / `skip` | `suffix` |
| `--date-prefix` | Префикс даты `YYYY-MM-DD-` | Выключен |
| `--block-ids` | Генерация `^block-id` для параграфов | Выключено |
| `--user-agent` | Переопределить User-Agent | Браузерный |
| `--delay` | Задержка между запросами (сек) | `0` |

### Python API

#### Базовое использование

```python
from markdownurl import fetch_article, ArticleResult

result = fetch_article("https://example.com/article")

print(result.title)          # "Заголовок статьи"
print(result.markdown)       # Markdown-контент (str)
print(result.frontmatter)    # Свойства (dict)
print(result.success)        # True (bool)
print(result.filepath)       # Path к файлу или None (если skip/error)

result.save("output.md")     # Сохранить в файл
```

#### С кастомными параметрами

```python
result = fetch_article(
    "https://example.com/article",
    output_dir="notes/article.md",  # Путь к файлу или директории
    include_frontmatter=True,
    timeout=15,
    images="download",
    images_dir="assets/",
    link_format="wikilink",
    conflict="suffix",
    date_prefix=True,
    block_ids=False,
    user_agent="MyBot/1.0",
)
```

#### Пакетное извлечение

```python
from markdownurl import fetch_articles

results = fetch_articles(
    ["https://site1.com/a", "https://site2.com/b"],
    output_dir="notes/",
    delay=2.0,
)

for r in results:
    if r.success:
        print(f"OK: {r.filepath}")
    else:
        print(f"FAIL: {r.url} ({r.status})")
```

## Формат вывода

### YAML-фронтматтер

```yaml
---
title: "Заголовок статьи"
author: "Имя автора"
date: '2026-09-22'
source: "https://example.com/article"
tags:
  - web-clip
  - article
---
```

### Obsidian-элементы

| Элемент | Синтаксис | Пример |
|---------|-----------|--------|
| Wikilinks | `[[Note]]`, `[[Note\|Text]]` | Ссылки на заметки |
| Callouts | `> [!info] Заголовок` | Блоки информации |
| Эмбеды | `![[image.png]]`, `![[image.png\|300]]` | Встроенные изображения |
| Выделение | `==текст==` | Маркировка важного |
| Комментарии | `%%скрытый текст%%` | Скрытый контент |
| Block IDs | `^block-id` в конце параграфа | Ссылки на блоки |

## Сравнение с альтернативами

| Критерий | Плагины Obsidian | MarkdownURL |
|----------|:---:|:---:|
| Запуск без Obsidian | — | ✅ |
| CLI | — | ✅ |
| Python API | — | ✅ |
| Пакетный режим | — | ✅ |
| Wikilinks | Редко | ✅ |
| Callouts | — | ✅ |
| Скачивание изображений | — | ✅ |
| Интеграция с CI/CD | — | ✅ |

## Безопасность

MarkdownURL включает защиту от распространённых уязвимостей:

- **SSRF-защита** — при скачивании изображений блокируются запросы к внутренним IP-адресам (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, ::1, fc00::/7 и др.)
- **Валидация URL** — проверка формата и схемы URL перед отправкой запроса (только http/https)
- **Экранирование callouts** — спецсимволы `>` и `!` в заголовках и теле callout экранируются для предотвращения Markdown-инъекций

> [!warning]
> Инструмент предназначен для использования с доверенными источниками. Не используйте с неизвестными или вредоносными URL.

## Архитектура

```
markdownurl/
├── __init__.py          # API: fetch_article, fetch_articles
├── __main__.py          # python -m markdownurl
├── cli.py               # CLI-интерфейс (click)
├── converter.py         # Постобработка Markdown
├── exceptions.py        # Кастомные исключения
├── extractor.py         # Извлечение контента (trafilatura)
├── fetcher.py           # HTTP-клиент (httpx, retry, URL validation)
├── frontmatter.py       # YAML-фронтматтер (PyYAML)
├── images.py            # Скачивание изображений (SSRF protection)
├── namer.py             # Генерация имён файлов
└── translations.py      # i18n (ru/en)
```

## Лицензия

GPL-3.0
