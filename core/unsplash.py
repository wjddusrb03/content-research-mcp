"""Unsplash API client for photo search."""

import os

import httpx


def is_available() -> bool:
    """Check if Unsplash API key is configured."""
    return bool(os.environ.get("UNSPLASH_ACCESS_KEY"))


def _get_access_key() -> str:
    """Return the Unsplash access key from environment variables."""
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not access_key:
        raise RuntimeError(
            "Unsplash API key not set. Get your free key at https://unsplash.com/developers "
            "and add UNSPLASH_ACCESS_KEY to your .env file."
        )
    return access_key


def search_photos(query: str, per_page: int = 5) -> list[dict]:
    """Search Unsplash photos.

    Args:
        query: Search keyword.
        per_page: Number of results per page (default: 5).

    Returns:
        List of photo dicts with id, description, url_regular, url_small,
        photographer, photographer_url, download_link.
    """
    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {_get_access_key()}"}
    params = {"query": query, "per_page": per_page}

    with httpx.Client() as client:
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()

    results = resp.json().get("results", [])
    return [
        {
            "id": photo.get("id", ""),
            "description": photo.get("description") or photo.get("alt_description", ""),
            "url_regular": photo.get("urls", {}).get("regular", ""),
            "url_small": photo.get("urls", {}).get("small", ""),
            "photographer": photo.get("user", {}).get("name", ""),
            "photographer_url": photo.get("user", {}).get("links", {}).get("html", ""),
            "download_link": photo.get("links", {}).get("download", ""),
        }
        for photo in results
    ]
