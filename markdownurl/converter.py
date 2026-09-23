"""Постобработка Markdown: ссылки, callouts, highlights, Mermaid, wikilinks."""

from __future__ import annotations

import hashlib
import re
from html import unescape
from urllib.parse import urljoin

# Regex-паттерны для callouts (вынесены для переиспользования)
_BLOCKQUOTE_CLASS_RE = re.compile(
    r'<blockquote[^>]*class\s*=\s*["\']([^"\']*)["\'][^>]*>(.*?)</blockquote>',
    re.DOTALL | re.IGNORECASE,
)
_BLOCKQUOTE_TITLE_RE = re.compile(
    r'<p[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE
)


def _escape_callout_field(text: str) -> str:
    """Экранировать спецсимволы > и ! в полях callout для предотвращения инъекции Markdown.

    Args:
        text: Исходный текст для экранирования.

    Returns:
        Текст с экранированными спецсимволами.
    """
    if not text:
        return text
    # Экранируем > и ! внутри текста callout
    # Заменяем > на \> и ! на \! для предотвращения Markdown-инъекций
    # Исключение: символы в начале строки после > (часть цитаты)
    lines = text.split('\n')
    escaped_lines: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('>'):
            # Часть цитаты — пропускаем
            escaped_lines.append(line)
        else:
            # Экранируем > и ! внутри текста
            escaped = re.sub(r'>', r'\\>', line)
            escaped = re.sub(r'!', r'\\!', escaped)
            escaped_lines.append(escaped)
    return '\n'.join(escaped_lines)


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

        # 0. Убрать ¶ (U+00B6) и zero-width space (U+200B)
        text = re.sub(r'[\u00b6\u200b]', '', text)

        # 0.1 Конвертация HTML-тегов форматирования → Markdown
        text = self._convert_formatting_tags(text)

        # 0.2 Параметры функций *param* → `param`
        text = self._convert_function_params(text)

        # 0.3 HTML-списки → Markdown-списки (ДО shell-команд, чтобы не трогать ``` блоки)
        text = self._fix_html_lists(text)

        # 0.4 Shell-команды → ```bash (ПОСЛЕ списков, чтобы не конфликтовать)
        text = self._convert_shell_commands(text)

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

        # 7. Конвертация ссылок
        if link_format == "wikilink":
            text = self._to_wikilinks(text)
        elif link_format == "markdown":
            text = self._to_markdown_links(text)

        # 8. Добавление block IDs (опционально)
        if block_ids:
            text = self._add_block_ids(text)

        return text

    def _convert_formatting_tags(self, text: str) -> str:
        """Конвертировать HTML-теги форматирования в Markdown."""
        # <del>, <s>, <strike> → ~~текст~~
        text = re.sub(
            r'<(del|s|strike)[^>]*>(.*?)</\1>',
            r'~~\2~~',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return text

    def _convert_function_params(self, text: str) -> str:
        """Конвертировать *param* в `param` для сигнатур функций.

        trafilatura извлекает параметры как *param_name*, которые markdownify
        превратил бы в курсив. Для API-документации это нужно исправить.

        Regex ищет *param* в контексте скобок: (*param*), (*param1*, *param2*),
        чтобы избежать ложных срабатываний на Markdown-курсиве.
        """
        # (*param*) → (`param`) — одиночный параметр
        text = re.sub(
            r'\(\*([^*]+)\*\)',
            r'(`\1`)',
            text,
        )
        # (*param1*, *param2*) → (`param1`, `param2`) — несколько параметров
        text = re.sub(
            r'\(\*([^*]+)\*,\s*\*([^*]+)\*\)',
            r'(`\1`, `\2`)',
            text,
        )
        return text

    def _convert_shell_commands(self, text: str) -> str:
        """Оборачивает строки shell-команд в ```bash блоки.

        Распознаёт команды, начинающиеся с:
        - export, sudo, cd, find, grep, cat, echo, pip, apt, etc.
        - строки, состоящие только из команд и аргументов
        """
        shell_keywords = (
            'export', 'sudo', 'cd', 'find', 'grep', 'cat', 'echo',
            'pip', 'apt', 'aptitude', 'apt-get', 'make', 'emake',
            'doas', 'ebuild', 'tar', 'wget', 'curl', 'rm', 'mv',
            'cp', 'chmod', 'chown', 'ls', 'mkdir', 'head', 'tail',
            'sed', 'awk', 'xargs', 'sort', 'uniq', 'wc', 'diff',
            'git', 'hg', 'svn', 'npm', 'yarn', 'go', 'rustc',
            'python', 'python3', 'node', 'ruby', 'php', 'java',
            'gcc', 'g++', 'clang', 'cmake', 'docker', 'kubectl',
            'print0', 'set', 'unset', 'source',
            'eval', 'alias', 'unalias', 'function',
        )

        lines = text.split('\n')
        result: list[str] = []
        in_code_block = False
        buffer: list[str] = []

        def _is_shell_line(line: str) -> bool:
            stripped = line.strip()
            if not stripped:
                return False
            # Пропускаем строки, которые уже являются частью markdown-структур
            if stripped.startswith(('```', '#', '>', '|')):
                return False
            # Пропускаем строки с маркерами списков (- , * , + , 1. )
            if re.match(r'^[-*+]\s', stripped):
                return False
            if re.match(r'^\d+\.\s', stripped):
                return False
            if stripped.startswith(shell_keywords):
                return True
            # Строка вида: VAR="value"
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', stripped):
                return True
            # Строка с операторами: &&, ||, |, >, >>, ;
            if re.match(r'^[|;&>]+', stripped):
                return True
            # Строка вида: GOPROXY=... go ...
            return bool(re.match(r'^[A-Z_]+=.*\s+go\s+', stripped))

        def _flush_buffer() -> None:
            nonlocal buffer
            if len(buffer) >= 1:
                result.append('```bash')
                result.extend(buffer)
                result.append('```')
            buffer = []

        for line in lines:
            # Внутри ``` блоков не трогаем
            if line.strip().startswith('```'):
                if in_code_block:
                    in_code_block = False
                else:
                    _flush_buffer()
                    in_code_block = True
                result.append(line)
                continue

            if not in_code_block and _is_shell_line(line):
                if buffer:
                    _flush_buffer()
                buffer.append(line)
            else:
                if buffer:
                    _flush_buffer()
                result.append(line)

        if buffer:
            _flush_buffer()

        return '\n'.join(result)

    def _fix_html_lists(self, text: str) -> str:
        """Попытка восстановить Markdown-списки из артефактов trafilatura.

        trafilatura извлекает <li> как текст без префиксов `- ` или `1. `.
        Эта функция пытается распознать вложенные списки по отступам.
        """
        lines = text.split('\n')
        result: list[str] = []
        in_code_block = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Пропускаем строки внутри ``` блоков
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                result.append(line)
                i += 1
                continue

            if in_code_block:
                result.append(line)
                i += 1
                continue

            # Проверяем, является ли строка элементом списка без маркера
            # (имеет отступ и не начинается с `- `, `* `, `+ `, `1. `)
            indent = len(line) - len(line.lstrip())

            # Пропускаем строки, которые уже имеют маркеры
            if stripped and re.match(r'^[-*+]\s', stripped):
                result.append(line)
                i += 1
                continue
            if stripped and re.match(r'^\d+\.\s', stripped):
                result.append(line)
                i += 1
                continue

            if stripped and not any(
                stripped.startswith(prefix)
                for prefix in ('- ', '* ', '+ ', '1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ', '0. ')
            ) and not stripped.startswith('#') and not stripped.startswith('>'):
                # Это потенциальный элемент списка
                # Определяем уровень вложенности по отступу
                level = indent // 2  # 2 пробела = 1 уровень
                bullet = '-'
                if level > 0:
                    bullet = '*' if level % 3 == 1 else '+' if level % 3 == 2 else '-'

                # Проверяем, что следующая строка тоже элемент списка
                # (имеет больший или равный отступ)
                if i + 1 < len(lines):
                    next_stripped = lines[i + 1].strip()
                    next_indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                    if next_stripped and next_indent >= indent:
                        # Это элемент списка — добавляем маркер
                        prefix = ' ' * (level * 2) + bullet + ' '
                        result.append(prefix + stripped)
                        i += 1
                        # Обрабатываем последовательные элементы списка
                        while i < len(lines):
                            curr_stripped = lines[i].strip()
                            curr_indent = len(lines[i]) - len(lines[i].lstrip())
                            # Пропускаем строки с маркерами и внутри ```
                            if curr_stripped and re.match(r'^[-*+]\s', curr_stripped):
                                break
                            if curr_stripped and re.match(r'^\d+\.\s', curr_stripped):
                                break
                            if curr_stripped and curr_indent >= indent:
                                next_level = curr_indent // 2
                                next_bullet = '*' if next_level % 3 == 1 else '+' if next_level % 3 == 2 else '-'
                                prefix = ' ' * (next_level * 2) + next_bullet + ' '
                                result.append(prefix + curr_stripped)
                                i += 1
                            else:
                                break
                        continue

            result.append(line)
            i += 1

        return '\n'.join(result)

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

        bq_match = _BLOCKQUOTE_CLASS_RE.search(full_block)

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
                title_match = _BLOCKQUOTE_TITLE_RE.search(content)
                title = title_match.group(1).strip() if title_match else ""
                body = re.sub(
                    r'<p[^>]*>(.*?)</p>', r'\1\n', content,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                body = body.strip()
                body = re.sub(r'<[^>]+>', '', body)

                # Экранируем спецсимволы для предотвращения инъекции Markdown
                title = _escape_callout_field(title)
                body = _escape_callout_field(body)

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

    def _to_markdown_links(self, text: str) -> str:
        """Конвертировать wikilinks в markdown-ссылки."""
        def _replace(match: re.Match) -> str:
            wikilink = match.group(0)
            inner = wikilink[2:-2]  # Remove [[ and ]]
            if "|" in inner:
                alias, target = inner.split("|", 1)
                return f"[{alias}]({target})"
            return f"[{inner}]({inner})"

        # Match [[text]] or [[text|alias]] but not ![image]] or [[[nested
        text = re.sub(
            r'(?<!!)\[\[([^\]]+)\]\]',
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

            # Пропускаем строки, которые состоят только из ^block-id (артефакты извлечения)
            if re.match(r'^\s*-?\s*\^[a-f0-9]{8}\s*$', stripped):
                continue

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
