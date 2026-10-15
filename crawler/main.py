import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from check_source import cache_path, fetch_page, read_cache, save_cache
from themes import THEMES

ROOT = Path(__file__).resolve().parents[1]
THEMES_DIR = ROOT / "data" / "themes"
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


def get_source(theme, now):
    cached = read_cache(theme, now)

    if cached is not None:
        print(f"[{theme.theme_id}] SOURCE: cache")
        return cached, "cache"

    page = fetch_page(theme)
    cached = {
        **page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    save_cache(theme, cached)

    print(f"[{theme.theme_id}] SOURCE: API")
    return cached, "api"


def build_theme(theme, source):
    return {
        "schema_version": "1.0.0",
        "theme_id": theme.theme_id,
        "canonical_name": theme.canonical_name,
        "aliases": sorted(set(theme.aliases)),
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


def update_theme(theme, now, started_at):
    target = THEMES_DIR / f"{theme.theme_id}.json"

    try:
        source, source_used = get_source(theme, now)
        current = build_theme(theme, source)

        previous = None
        if target.exists():
            previous = json.loads(target.read_text(encoding="utf-8"))

        changed = previous != current

        if changed:
            write_json(target, current)
            print(f"UPDATED: data/themes/{theme.theme_id}.json")
        else:
            print(f"UNCHANGED: data/themes/{theme.theme_id}.json")

        return {
            "theme_id": theme.theme_id,
            "result": "success",
            "source_used": source_used,
            "source_fetched_at": source["fetched_at"],
            "content_changed": changed,
        }

    except Exception as error:
        print(
            f"FAILED: {theme.theme_id}: {type(error).__name__}",
            file=sys.stderr,
        )
        return {
            "theme_id": theme.theme_id,
            "result": "failure",
            "error_type": type(error).__name__,
        }


def main():
    started_at = datetime.now(timezone.utc).isoformat()
    now = datetime.now(timezone.utc)

    results = [update_theme(theme, now, started_at) for theme in THEMES]

    failed = [result for result in results if result["result"] == "failure"]

    write_json(STATUS, {
        "schema_version": "1.0.0",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "result": "failure" if failed else "success",
        "theme_count": len(THEMES),
        "failure_count": len(failed),
        "themes": results,
    })

    write_json(ROOT / "site" / "themes.json", {
        "schema_version": "1.0.0",
        "themes": [
            {
                "theme_id": theme.theme_id,
                "canonical_name": theme.canonical_name,
            }
            for theme in THEMES
        ],
    })

    print("STATUS: saved public theme list")
    print("STATUS: saved internal execution report")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()