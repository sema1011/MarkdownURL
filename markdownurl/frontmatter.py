"""Генерация YAML-фронтматера по правилам Obsidian Properties (1.9+)."""

from __future__ import annotations

from datetime import date
from typing import Any

import yaml

from markdownurl.extractor import ArticleMetadata


class FrontmatterGenerator:
    """Генерация YAML-фронтматера в формате Obsidian Properties."""

    def generate(
        self,
        meta: ArticleMetadata,
        source_url: str,
        include_frontmatter: bool = True,
    ) -> str:
        """Сгенерировать YAML-фронтматер.

        Args:
            meta: Извлечённые метаданные статьи.
            source_url: Исходный URL.
            include_frontmatter: Если False — вернуть пустую строку.

        Returns:
            YAML-блок, обрамлённый `---`, или пустая строка.
        """
        if not include_frontmatter:
            return ""

        props: dict[str, Any] = {}

        # title — обязательное поле, Text
        title = meta.title or "Untitled"
        props["title"] = title

        # source — обязательное поле, Text
        props["source"] = source_url

        # author — Text
        if meta.author:
            props["author"] = meta.author

        # date — Date (YYYY-MM-DD), fallback на текущую дату
        if meta.date:
            props["date"] = meta.date
        else:
            props["date"] = date.today().isoformat()

        # tags — Tags (список, НЕ строка)
        tags = meta.tags or ["web-clip"]
        props["tags"] = tags

        # aliases — List (если og:title отличается от title)
        if meta.og_title and meta.og_title != meta.title:
            props["aliases"] = [meta.og_title]

        # description — Text
        if meta.description:
            props["description"] = meta.description

        return self._dump_yaml(props)

    def _dump_yaml(self, props: dict[str, Any]) -> str:
        """Сериализовать свойства в YAML-блок через PyYAML."""
        yaml_content = yaml.safe_dump(
            props,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        return f"---\n{yaml_content}---"

    def to_dict(self, meta: ArticleMetadata, source_url: str) -> dict[str, Any]:
        """Вернуть свойства как dict (для тестирования)."""
        props: dict[str, Any] = {}

        title = meta.title or "Untitled"
        props["title"] = title

        props["source"] = source_url

        if meta.author:
            props["author"] = meta.author

        if meta.date:
            props["date"] = meta.date
        else:
            props["date"] = date.today().isoformat()

        tags = meta.tags or ["web-clip"]
        props["tags"] = tags

        if meta.og_title and meta.og_title != meta.title:
            props["aliases"] = [meta.og_title]

        if meta.description:
            props["description"] = meta.description

        return props
