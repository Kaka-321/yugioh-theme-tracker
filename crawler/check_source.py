import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "yugipedia-blue-eyes.json"
CACHE_TTL = timedelta(days=30)

API_URL = "https://yugipedia.com/api.php"
USER_AGENT = (
    "YugiohThemeTracker/0.1 "
    "(contact: https://github.com/Kaka-321/yugioh-theme-tracker/issues)"
)


def read_cache(now):
    if not CACHE.exists():
        return None

    try:
        cached = json.loads(CACHE.read_text(encoding="utf-8"))
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


def fetch_page():
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": "Blue-Eyes",
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


def main():
    now = datetime.now(timezone.utc)
    result = read_cache(now)

    if result is not None:
        print("CACHE HIT: no API request")
    else:
        result = fetch_page()
        result["fetched_at"] = now.isoformat()

        CACHE.parent.mkdir(parents=True, exist_ok=True)
        temporary = CACHE.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(CACHE)

        print("FETCHED: saved API result to local cache")

    print("Title:", result["title"])
    print("URL:", result["url"])


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
        print("FAILED:", error, file=sys.stderr)
        sys.exit(1)
