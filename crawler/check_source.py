import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from themes import Theme

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / ".cache"
CACHE_TTL = timedelta(days=30)

API_URL = "https://yugipedia.com/api.php"
USER_AGENT = (
    "YugiohThemeTracker/0.1 "
    "(contact: https://github.com/Kaka-321/yugioh-theme-tracker/issues)"
)


def cache_path(theme: Theme) -> Path:
    return CACHE_DIR / f"yugipedia-{theme.theme_id}.json"


def read_cache(theme: Theme, now: datetime):
    cache = cache_path(theme)

    if not cache.exists():
        return None

    try:
        cached = json.loads(cache.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(cached["fetched_at"])
        age = now - fetched_at

        if (
            timedelta(0) <= age < CACHE_TTL
            and isinstance(cached["title"], str)
            and isinstance(cached["url"], str)
        ):
            return cached
    except (ValueError, KeyError, TypeError, OSError):
        pass

    return None


def fetch_page(theme: Theme):
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": theme.source_title,
        "prop": "info",
        "inprop": "url",
        "redirects": "1",
        "maxlag": "5",
    }

    request = Request(
        API_URL + "?" + urlencode(params),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if "error" in payload:
        raise ValueError(
            "API error: "
            + json.dumps(payload["error"], ensure_ascii=False)
        )

    pages = payload.get("query", {}).get("pages", [])
    if len(pages) != 1:
        raise ValueError("Unexpected page count")

    page = pages[0]
    if "missing" in page or "invalid" in page:
        raise ValueError("Page is missing or invalid")

    title = page.get("title")
    url = page.get("fullurl")

    if not isinstance(title, str) or not isinstance(url, str):
        raise ValueError("Required page information is missing")

    return {"title": title, "url": url}


def save_cache(theme: Theme, value: dict) -> None:
    cache = cache_path(theme)
    cache.parent.mkdir(parents=True, exist_ok=True)

    temporary = cache.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(cache)


def main():
    now = datetime.now(timezone.utc)
    theme = Theme(
        theme_id="blue-eyes",
        canonical_name="青眼",
        aliases=("ブルーアイズ", "Blue-Eyes"),
        source_title="Blue-Eyes",
        source_url="https://yugipedia.com/wiki/Blue-Eyes",
    )

    result = read_cache(theme, now)

    if result is not None:
        print("CACHE HIT: no API request")
    else:
        result = fetch_page(theme)
        result["fetched_at"] = now.isoformat()
        save_cache(theme, result)
        print("FETCHED: saved API result to local cache")

    print("Title:", result["title"])
    print("URL:", result["url"])


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
        print("FAILED:", error, file=sys.stderr)
        sys.exit(1)