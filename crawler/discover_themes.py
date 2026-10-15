import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from themes import THEMES

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "internal" / "theme_candidates.json"

API_URL = "https://yugipedia.com/api.php"
CATEGORY_TITLE = "Category:Archetypes"
USER_AGENT = (
    "YugiohThemeTracker/0.1 "
    "(contact: https://github.com/Kaka-321/yugioh-theme-tracker/issues)"
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def api_request(params):
    request = Request(
        API_URL + "?" + urlencode(params),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=30) as response:
        return json.load(response)


def discover_archetype_titles():
    titles = []
    continuation = {}

    while True:
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "list": "categorymembers",
            "cmtitle": CATEGORY_TITLE,
            "cmlimit": "500",
            "cmtype": "page",
            **continuation,
        }

        payload = api_request(params)

        if "error" in payload:
            raise ValueError(
                "API error: "
                + json.dumps(payload["error"], ensure_ascii=False)
            )

        members = payload.get("query", {}).get("categorymembers", [])

        for member in members:
            title = member.get("title")
            if isinstance(title, str):
                titles.append(title)

        continuation = payload.get("continue", {})

        if not continuation:
            break

        time.sleep(1)

    return sorted(set(titles))


def main():
    now = datetime.now(timezone.utc).isoformat()
    registered_titles = {theme.source_title for theme in THEMES}
    discovered_titles = discover_archetype_titles()

    candidates = [
        {
            "source_title": title,
            "source_url": f"https://yugipedia.com/wiki/{title.replace(' ', '_')}",
            "status": "pending",
        }
        for title in discovered_titles
        if title not in registered_titles
    ]

    write_json(CANDIDATES, {
        "schema_version": "1.0.0",
        "discovered_at": now,
        "category": CATEGORY_TITLE,
        "registered_count": len(registered_titles),
        "discovered_count": len(discovered_titles),
        "pending_count": len(candidates),
        "candidates": candidates,
    })

    print(f"Discovered: {len(discovered_titles)} archetype pages")
    print(f"Registered: {len(registered_titles)} themes")
    print(f"Pending candidates: {len(candidates)}")
    print(f"Saved: {CANDIDATES.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
        print("FAILED:", error, file=sys.stderr)
        sys.exit(1)