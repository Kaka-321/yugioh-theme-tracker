import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from check_source import CACHE, fetch_page, read_cache

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "themes" / "blue-eyes.json"
STATUS = ROOT / "data" / "internal" / "status.json"


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


def get_source():
    now = datetime.now(timezone.utc)
    cached = read_cache(now)

    if cached is not None:
        print("SOURCE: cache")
        return cached, "cache"

    page = fetch_page()
    cached = {
        **page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(CACHE, cached)

    print("SOURCE: API")
    return cached, "api"


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
    started_at = datetime.now(timezone.utc).isoformat()

    try:
        source, source_used = get_source()
        current = build_theme(source)

        previous = None
        if TARGET.exists():
            previous = json.loads(TARGET.read_text(encoding="utf-8"))

        changed = previous != current

        if changed:
            write_json(TARGET, current)
            print("UPDATED: data/themes/blue-eyes.json")
        else:
            print("UNCHANGED: data/themes/blue-eyes.json")

        write_json(STATUS, {
            "schema_version": "1.0.0",
            "theme_id": "blue-eyes",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "result": "success",
            "source_used": source_used,
            "source_fetched_at": source["fetched_at"],
            "content_changed": changed,
        })

        print("STATUS: saved internal execution report")

    except Exception as error:
        write_json(STATUS, {
            "schema_version": "1.0.0",
            "theme_id": "blue-eyes",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "result": "failure",
            "error_type": type(error).__name__,
        })
        print(
            "FAILED: " + type(error).__name__,
            file=sys.stderr,
        )
        raise


if __name__ == "__main__":
    main()
