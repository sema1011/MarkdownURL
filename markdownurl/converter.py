"""Постобработка Markdown: ссылки, callouts, highlights, Mermaid, wikilinks."""

from __future__ import annotations

import hashlib
import re
from html import unescape
from urllib.parse import urljoin


class Converter:
    """Постобработка Markdown-контента для Obsidian."""

    CALLOUT_TYPES = {
        "note", "info", "tip", "warning", "danger", "error",
        "bug", "example", "quote", "success", "question",
        "failure", "abstract", "tldr", "todo",
    }

    def convert(
        self,
        markdown: str,
        url: str = "",
        link_format: str = "wikilink",
        block_ids: bool = False,
    ) -> str:
        """Преобразовать Markdown в Obsidian Flavored Markdown.

        Args:
            markdown: Исходный Markdown-контент.
            url: Исходный URL (для абсолютных ссылок).
            link_format: Формат ссылок — 'wikilink' или 'markdown'.
            block_ids: Добавлять ли block IDs.

        Returns:
            Преобразованный Markdown.
        """
        text = markdown

        # 1. Конвертация <mark> → ==текст==
        text = self._convert_highlights(text)

        # 2. Конвертация <!-- comment --> → %%comment%%
        text = self._convert_comments(text)

        # 3. Конвертация blockquote с классами → callouts
        text = self._convert_callouts(text)

        # 4. Конвертация <pre class="mermaid"> → ```mermaid
        text = self._convert_mermaid(text)

        # 5. Конвертация математики: <math> → $...$/$$...$$, затем <span class="math"> → $...$
        #    Порядок важен: сначала внутренние <math>, потом внешние <span class="math">
        text = self._convert_math(text)

        # 6. Конвертация относительных ссылок в абсолютные
        if url:
            text = self._absolute_links(text, url)

        # 7. Конвертация ссылок в wikilinks (опционально)
        if link_format == "wikilink":
            text = self._to_wikilinks(text)

        # 8. Добавление block IDs (опционально)
        if block_ids:
            text = self._add_block_ids(text)

        return text

    def _convert_highlights(self, text: str) -> str:
        """Конвертировать <mark>...</mark> в ==текст==."""
        return re.sub(
            r"<mark[^>]*>(.*?)</mark>",
            r"==\1==",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

    def _convert_comments(self, text: str) -> str:
        """Конвертировать <!-- comment --> в %%comment%%."""
        return re.sub(
            r"<!--(.*?)-->",
            r"%%\1%%",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

    def _convert_math(self, text: str) -> str:
        """Конвертировать <math> и <span class="math"> в $...$ / $$...$$.

        Порядок важен: сначала <math display="block"> (блок), потом <math> (инлайн),
        потом <span class="math"> (обёртка), чтобы избежать двойного преобразования.
        """
        # Block math: <math display="block">...</math> — ДО инлайнового
        text = re.sub(
            r'<math[^>]*display\s*=\s*["\']block["\'][^>]*>(.*?)</math>',
            r'$$\1$$',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        # Inline math: <math>...</math>
        text = re.sub(
            r'<math[^>]*>(.*?)</math>',
            r'$\1$',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        # Inline math: <span class="math">...</span>
        text = re.sub(
            r'<span\s+class\s*=\s*["\']math["\']>(.*?)</span>',
            r'$\1$',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return text

    def _convert_callouts(self, text: str) -> str:
        """Конвертировать blockquote с классами в Obsidian callouts."""
        lines = text.split("\n")
        result: list[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if line.startswith("> ") or line.startswith(">"):
                block_lines: list[str] = [line]
                j = i + 1
                while j < len(lines):
                    if lines[j].startswith("> ") or lines[j] == ">":
                        block_lines.append(lines[j])
                        j += 1
                    else:
                        break

                converted = self._parse_blockquote_block(block_lines)
                result.extend(converted)
                i = j
            else:
                result.append(line)
                i += 1

        return "\n".join(result)

    def _parse_blockquote_block(self, block_lines: list[str]) -> list[str]:
        """Преобразовать блок blockquote в callout или обычную цитату."""
        full_block = "\n".join(block_lines)

        bq_match = re.search(
            r'<blockquote[^>]*class\s*=\s*["\']([^"\']*)["\'][^>]*>(.*?)</blockquote>',
            full_block,
            re.DOTALL | re.IGNORECASE,
        )

        if bq_match:
            classes = bq_match.group(1).strip().split()
            content = bq_match.group(2).strip()

            callout_type = None
            for cls in classes:
                cls_lower = cls.lower().strip()
                if cls_lower in self.CALLOUT_TYPES:
                    callout_type = cls_lower
                    break
                if cls_lower.startswith("callout-"):
                    callout_type = cls_lower.replace("callout-", "")
                    if callout_type in self.CALLOUT_TYPES:
                        break

            if callout_type:
                title_match = re.search(
                    r'<p[^>]*>(.*?)</p>', content, re.DOTALL | re.IGNORECASE
                )
                title = title_match.group(1).strip() if title_match else ""
                body = re.sub(
                    r'<p[^>]*>(.*?)</p>', r'\1\n', content,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                body = body.strip()
                body = re.sub(r'<[^>]+>', '', body)

                if title:
                    return [
                        f"> [!{callout_type}] {title}",
                        f"> {body}" if body else "",
                    ]
                return [
                    f"> [!{callout_type}]",
                    f"> {body}" if body else "",
                ]

        return block_lines

    def _convert_mermaid(self, text: str) -> str:
        """Конвертировать <pre class="mermaid"> в ```mermaid ... ```."""
        def _mermaid_replace(match: re.Match) -> str:
            content = match.group(1).strip()
            content = unescape(content)
            return f"```mermaid\n{content}\n```"

        return re.sub(
            r'<pre\s+class\s*=\s*["\']mermaid["\'][^>]*>(.*?)</pre>',
            _mermaid_replace,
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

    def _absolute_links(self, text: str, base_url: str) -> str:
        """Конвертировать относительные ссылки в абсолютные."""

        def _replace_link(match: re.Match) -> str:
            prefix = match.group(1) or ""
            link_text = match.group(2)
            url = match.group(3)

            if not url.startswith(("http://", "https://", "mailto:", "#", "data:")):
                url = urljoin(base_url, url)

            return f"{prefix}[{link_text}]({url})"

        text = re.sub(
            r'(!?)\[(.*?)\]\(([^)]+)\)',
            _replace_link,
            text,
        )

        return text

    def _to_wikilinks(self, text: str) -> str:
        """Конвертировать внешние ссылки в wikilinks (частично)."""
        def _replace(match: re.Match) -> str:
            prefix = match.group(1) or ""
            link_text = match.group(2)
            url = match.group(3)

            if prefix == "!":
                return match.group(0)

            if url.startswith(("http://", "https://", "mailto:", "#", "data:")):
                return match.group(0)

            return f"{prefix}[[{link_text or url}]]"

        text = re.sub(
            r'(!?)\[(.*?)\]\(([^)]+)\)',
            _replace,
            text,
        )

        return text

    def _add_block_ids(self, text: str) -> str:
        """Добавить ^block-id к ключевым параграфам."""
        lines = text.split("\n")
        result: list[str] = []

        for line in lines:
            stripped = line.strip()

            skip_patterns = [
                (lambda s: not s),
                (lambda s: s.startswith("---")),
                (lambda s: s.startswith("#")),
                (lambda s: s.startswith(">")),
                (lambda s: s.startswith("- ")),
                (lambda s: s.startswith("* ")),
                (lambda s: s.startswith("|")),
                (lambda s: s.startswith("```")),
                (lambda s: s.startswith("![")),
                (lambda s: s.startswith("[!")),
            ]

            skip = False
            for check in skip_patterns:
                if check(stripped):
                    skip = True
                    break

            if skip:
                result.append(line)
                continue

            block_id = hashlib.md5(stripped.encode()).hexdigest()[:8]
            suffix = f" ^{block_id}"

            if re.search(r'\s\^[a-zA-Z0-9_-]+$', stripped):
                result.append(line)
            else:
                result.append(line.rstrip() + suffix)

        return "\n".join(result)
