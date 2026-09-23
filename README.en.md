# MarkdownURL

Extract web articles from the internet and save them as **Obsidian Flavored Markdown** — with YAML frontmatter, wikilinks, callouts, image embeds, and other Obsidian syntax extensions.

Runs **outside** Obsidian — from the terminal, a script, cron, or a CI/CD pipeline. Does not require Obsidian to be running.

## Features

- **Content extraction** — automatic detection of the main article text, removal of ads, navigation, and other noise.
- **Obsidian Flavored Markdown** — wikilinks, callouts (`> [!info]`), image embeds (`![[image.png]]`), highlights (`==text==`), comments (`%%text%%`).
- **YAML frontmatter** — Obsidian properties (`title`, `author`, `date`, `tags`, `source`, etc.).
- **Image downloading** — local storage in an `attachments/` folder with embeds.
- **Batch processing** — multiple URLs from arguments or a file.
- **Flexible configuration** — link formats, conflict handling, date prefix, block IDs.

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Then install the package from source:

```bash
pip install -e .
```

> [!note]
> The package is not published on PyPI and is intended for local use only.

## Usage

### CLI

#### Single article

```bash
# Basic usage
markdownurl https://example.com/article

# Save to a specific file
markdownurl https://example.com/article --output notes/my-article.md

# Download images to attachments/
markdownurl https://example.com/article --images download

# Standard Markdown (no wikilinks)
markdownurl https://example.com/article --link-format markdown

# Without frontmatter
markdownurl https://example.com/article --no-frontmatter
```

#### Batch processing

```bash
# Multiple URLs
markdownurl https://site1.com/article https://site2.com/article -o notes/

# From a file (one URL per line)
markdownurl --from-file urls.txt -o notes/ --delay 2
```

#### Full help

```bash
markdownurl --help
```

| Flag | Description | Default |
|------|-------------|:---:|
| `--output` | Path to file or directory | Current folder |
| `--from-file` | File with a list of URLs | — |
| `--no-frontmatter` | Disable YAML frontmatter | Enabled |
| `--timeout` | Request timeout (sec) | `10` |
| `--images` | `link` / `download` / `skip` | `link` |
| `--images-dir` | Folder for downloaded images | `attachments` |
| `--link-format` | `wikilink` / `markdown` | `wikilink` |
| `--conflict` | `suffix` / `overwrite` / `skip` | `suffix` |
| `--date-prefix` | Date prefix `YYYY-MM-DD-` | Disabled |
| `--block-ids` | Generate `^block-id` for paragraphs | Disabled |
| `--user-agent` | Override User-Agent | Browser |
| `--delay` | Delay between requests (sec) | `0` |

### Python API

#### Basic usage

```python
from markdownurl import fetch_article, ArticleResult

result = fetch_article("https://example.com/article")

print(result.title)          # "Article title"
print(result.markdown)       # Markdown content (str)
print(result.frontmatter)    # Properties (dict)
print(result.success)        # True (bool)
print(result.filepath)       # Path to file or None (if skip/error)

result.save("output.md")     # Save to file
```

#### With custom parameters

```python
result = fetch_article(
    "https://example.com/article",
    output_dir="notes/article.md",  # Path to file or directory
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

#### Batch extraction

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

## Output format

### YAML frontmatter

```yaml
---
title: "Article title"
author: "Author name"
date: '2026-09-22'
source: "https://example.com/article"
tags:
  - web-clip
  - article
---
```

### Obsidian elements

| Element | Syntax | Example |
|---------|--------|--------|
| Wikilinks | `[[Note]]`, `[[Note\|Text]]` | Links to notes |
| Callouts | `> [!info] Title` | Info blocks |
| Embeds | `![[image.png]]`, `![[image.png\|300]]` | Inline images |
| Highlights | `==text==` | Mark important text |
| Comments | `%%hidden text%%` | Hidden content |
| Block IDs | `^block-id` at end of paragraph | Links to blocks |

## Comparison with alternatives

| Criterion | Obsidian plugins | MarkdownURL |
|-----------|:---:|:---:|
| Runs without Obsidian | — | ✅ |
| CLI | — | ✅ |
| Python API | — | ✅ |
| Batch mode | — | ✅ |
| Wikilinks | Rare | ✅ |
| Callouts | — | ✅ |
| Image downloading | — | ✅ |
| CI/CD integration | — | ✅ |

## Architecture

```
markdownurl/
├── __init__.py          # API: fetch_article, fetch_articles
├── __main__.py          # python -m markdownurl
├── cli.py               # CLI interface (click)
├── converter.py         # Markdown post-processing
├── exceptions.py        # Custom exceptions
├── extractor.py         # Content extraction (trafilatura)
├── fetcher.py           # HTTP client (httpx, retry)
├── frontmatter.py       # YAML frontmatter (PyYAML)
├── images.py            # Image downloading
├── namer.py             # File name generation
└── translations.py      # i18n (ru/en)
```

## License

GPL-3.0
