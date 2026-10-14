import json
from datetime import datetime, timezone
from pathlib import Path

from check_source import CACHE, fetch_page, read_cache

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "themes" / "blue-eyes.json"


def get_source():
    now = datetime.now(timezone.utc)
    cached = read_cache(now)

    if cached is not None:
        print("SOURCE: cache")
        return {
            "title": cached["title"],
            "url": cached["url"],
        }

    page = fetch_page()
    cached = {
        **page,
        "fetched_at": now.isoformat(),
    }

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    temporary = CACHE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(cached, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(CACHE)

    print("SOURCE: API")
    return page


def build_theme(source):
    return {
        "schema_version": "1.0.0",
        "theme_id": "blue-eyes",
        "canonical_name": "青眼",
        "aliases": sorted({"ブルーアイズ", "Blue-Eyes"}),
        "source_mode": "api-metadata-and-manual",
        "source": {
            "provider": "Yugipedia",
            "title": source["title"],
            "url": source["url"],
        },
        "field_origins": {
            "canonical_name": "manual",
            "aliases": "manual",
            "source": "api",
        },
    }


def main():
    source = get_source()
    current = build_theme(source)

    if TARGET.exists():
        previous = json.loads(TARGET.read_text(encoding="utf-8"))
        if previous == current:
            print("UNCHANGED: data/themes/blue-eyes.json")
            return

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        current,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"

    temporary = TARGET.with_suffix(".json.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(TARGET)

    print("UPDATED: data/themes/blue-eyes.json")


if __name__ == "__main__":
    main()
