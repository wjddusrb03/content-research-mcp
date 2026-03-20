"""Naver API client for blog search, news search, trend data, and translation."""

import os
import re

import httpx


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text)


def is_available() -> bool:
    """Check if Naver API credentials are configured."""
    return bool(os.environ.get("NAVER_CLIENT_ID") and os.environ.get("NAVER_CLIENT_SECRET"))


def _get_credentials() -> tuple[str, str]:
    """Return (client_id, client_secret) from environment variables."""
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Naver API key not set. Get your free key at https://developers.naver.com "
            "and add NAVER_CLIENT_ID + NAVER_CLIENT_SECRET to your .env file."
        )
    return client_id, client_secret


def _headers() -> dict[str, str]:
    """Build request headers with Naver API credentials."""
    client_id, client_secret = _get_credentials()
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }


def search_blog(query: str, display: int = 10, sort: str = "sim") -> list[dict]:
    """Search Naver blogs.

    Args:
        query: Search keyword.
        display: Number of results (max 100).
        sort: Sort order - "sim" (relevance) or "date".

    Returns:
        List of blog post dicts with title, description, link, bloggername, postdate.
    """
    url = "https://openapi.naver.com/v1/search/blog"
    params = {"query": query, "display": display, "sort": sort}

    with httpx.Client() as client:
        resp = client.get(url, headers=_headers(), params=params)
        resp.raise_for_status()

    items = resp.json().get("items", [])
    return [
        {
            "title": _strip_html(item.get("title", "")),
            "description": _strip_html(item.get("description", "")),
            "link": item.get("link", ""),
            "bloggername": item.get("bloggername", ""),
            "postdate": item.get("postdate", ""),
        }
        for item in items
    ]


def search_news(query: str, display: int = 10, sort: str = "date") -> list[dict]:
    """Search Naver news.

    Args:
        query: Search keyword.
        display: Number of results (max 100).
        sort: Sort order - "date" (recent) or "sim" (relevance).

    Returns:
        List of news article dicts with title, description, originallink, pubDate.
    """
    url = "https://openapi.naver.com/v1/search/news"
    params = {"query": query, "display": display, "sort": sort}

    with httpx.Client() as client:
        resp = client.get(url, headers=_headers(), params=params)
        resp.raise_for_status()

    items = resp.json().get("items", [])
    return [
        {
            "title": _strip_html(item.get("title", "")),
            "description": _strip_html(item.get("description", "")),
            "originallink": item.get("originallink", ""),
            "pubDate": item.get("pubDate", ""),
        }
        for item in items
    ]


def get_trend(
    keywords: list[list[str]],
    start_date: str,
    end_date: str,
    time_unit: str = "month",
) -> dict:
    """Get Naver search trend data via DataLab API.

    Args:
        keywords: List of keyword groups. Each group is a list of strings
                  where the first element is used as the group name.
        start_date: Start date in "yyyy-mm-dd" format.
        end_date: End date in "yyyy-mm-dd" format.
        time_unit: Time unit - "date", "week", or "month".

    Returns:
        Full JSON response from the DataLab API.
    """
    url = "https://openapi.naver.com/v1/datalab/search"
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [
            {"groupName": kw[0], "keywords": kw} for kw in keywords
        ],
    }

    with httpx.Client() as client:
        resp = client.post(url, headers=_headers(), json=body)
        resp.raise_for_status()

    return resp.json()


def translate(text: str, source: str = "en", target: str = "ko") -> str:
    """Translate text using Naver Papago API.

    Args:
        text: Text to translate.
        source: Source language code (default: "en").
        target: Target language code (default: "ko").

    Returns:
        Translated text string.
    """
    url = "https://openapi.naver.com/v1/papago/n2mt"
    data = {"source": source, "target": target, "text": text}

    with httpx.Client() as client:
        resp = client.post(url, headers=_headers(), data=data)
        resp.raise_for_status()

    return resp.json()["message"]["result"]["translatedText"]
