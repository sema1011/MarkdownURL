"""Загрузка веб-страниц по URL."""

from __future__ import annotations

import re
import time

import httpx

from markdownurl.exceptions import FetchError, FetchTimeoutError

BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

# Регулярка для <meta charset="..."> или <meta http-equiv="Content-Type" content="text/html; charset=...">
_META_CHARSET = re.compile(
    r'<meta[^>]*charset\s*=\s*["\']?([^"\'>\s]+)', re.IGNORECASE
)
_META_CONTENT_TYPE = re.compile(
    r'<meta[^>]*http-equiv\s*=\s*["\']?content-type["\']?[^>]*content\s*=\s*["\']?[^"\']*charset=([^"\';\s]+)',
    re.IGNORECASE,
)


class Fetcher:
    """HTTP-клиент для загрузки веб-страниц."""

    def __init__(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
        user_agent: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or BROWSER_UA
        self.transport = transport

    def fetch(self, url: str) -> httpx.Response:
        """Загрузить страницу с повторными попытками при 5xx."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(
                    transport=self.transport,
                    follow_redirects=True,
                ) as client:
                    response = client.get(
                        url, headers=headers, timeout=self.timeout
                    )

                if response.status_code == 404:
                    raise FetchError(
                        url, "Страница не найдена", status_code=404
                    )

                if response.status_code >= 500:
                    last_exc = FetchError(
                        url,
                        f"Серверная ошибка (HTTP {response.status_code})",
                        status_code=response.status_code,
                    )
                    if attempt < self.max_retries:
                        # Экспоненциальная задержка: 1s, 2s, 4s
                        time.sleep(2 ** (attempt - 1))
                        continue
                    raise last_exc from None

                return response

            except httpx.TimeoutException:
                last_exc = FetchTimeoutError(url, self.timeout)
                if attempt < self.max_retries:
                    continue
                raise last_exc from None

            except httpx.RequestError as exc:
                last_exc = FetchError(url, f"Ошибка запроса: {exc}")
                if attempt < self.max_retries:
                    continue
                raise last_exc from None

        raise FetchError(url, "Max retries exceeded")

    @staticmethod
    def detect_encoding(text: str, response: httpx.Response) -> str:
        """Определить кодировку из HTTP-заголовков, meta-тегов или fallback UTF-8.

        Приоритет:
        1. Content-Type HTTP-заголовок
        2. <meta charset="...">
        3. <meta http-equiv="Content-Type" content="...charset=...">
        4. UTF-8
        """
        # 1. HTTP-заголовок
        content_type = response.headers.get("content-type", "")
        charset_match = re.search(r"charset=([^;\s]+)", content_type)
        if charset_match:
            return charset_match.group(1).strip()

        # 2. <meta charset="...">
        match = _META_CHARSET.search(text)
        if match:
            return match.group(1).strip()

        # 3. <meta http-equiv="Content-Type"...>
        match = _META_CONTENT_TYPE.search(text)
        if match:
            return match.group(1).strip()

        return "utf-8"

    def fetch_and_decode(self, url: str) -> tuple[str, str]:
        """Загрузить страницу и вернуть (текст, кодировка).

        Кодировка используется для декодирования ответа.
        """
        response = self.fetch(url)
        encoding = self.detect_encoding(response.text, response)
        # Перекодируем: httpx может вернуть байты с другой кодировкой
        raw = response.content
        try:
            decoded = raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            decoded = raw.decode("utf-8", errors="replace")
        return decoded, encoding
