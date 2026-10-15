import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "internal" / "theme_candidates.json"
THEMES_PATH = ROOT / "crawler" / "themes.py"


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    slug = slug.strip("-")
    return slug or "theme"


def build_entry(theme_id, canonical_name, source_title):
    return f'''    Theme(
        theme_id="{theme_id}",
        canonical_name="{canonical_name}",
        aliases=(),
        source_title="{source_title}",
        source_url="https://yugipedia.com/wiki/{source_title.replace(' ', '_')}",
    ),
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    data = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    themes_text = THEMES_PATH.read_text(encoding="utf-8")

    registered_titles = set(re.findall(r'source_title="([^"]+)"', themes_text))
    registered_ids = set(re.findall(r'theme_id="([^"]+)"', themes_text))

    added = []
    skipped = 0
    used_ids = set(registered_ids)

    for candidate in data["candidates"]:
        if len(added) >= args.limit:
            break

        title = candidate["source_title"]

        if title in registered_titles:
            skipped += 1
            continue

        if title.startswith("/"):
            skipped += 1
            continue

        if "(" in title:
            skipped += 1
            continue

        theme_id = slugify(title)
        base_id = theme_id
        number = 2

        while theme_id in used_ids:
            theme_id = f"{base_id}-{number}"
            number += 1

        used_ids.add(theme_id)
        registered_titles.add(title)

        entry = build_entry(theme_id, title, title)

        closing_index = themes_text.rfind(")")
        if closing_index == -1:
            raise ValueError("THEMES tuple closing parenthesis not found")

        themes_text = (
            themes_text[:closing_index].rstrip()
            + "\n"
            + entry
            + themes_text[closing_index:]
        )

        added.append(theme_id)

    THEMES_PATH.write_text(themes_text, encoding="utf-8")

    print(f"Added: {len(added)}")
    print(f"Skipped: {skipped}")
    print("Added IDs:")
    for theme_id in added:
        print(f"- {theme_id}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        sys.exit(1)