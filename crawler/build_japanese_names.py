import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEURON_CSV = ROOT / "data" / "internal" / "neuron_categories.csv"
CANDIDATES = ROOT / "data" / "internal" / "theme_candidates.json"
THEMES_PATH = ROOT / "crawler" / "themes.py"
OUTPUT = ROOT / "data" / "meta" / "japanese_names.json"
UNMATCHED = ROOT / "data" / "internal" / "japanese_names_unmatched.json"


def normalize(value):
    value = unicodedata.normalize("NFKC", value)
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def main():
    with NEURON_CSV.open(encoding="utf-8-sig", newline="") as file:
        neuron_rows = list(csv.DictReader(file))

    by_normalized_en = {}
    for row in neuron_rows:
        english_name = (row.get("name_en") or "").strip()
        japanese_name = (row.get("name_ja") or "").strip()

        if not english_name or not japanese_name:
            continue

        key = normalize(english_name)
        if key and key not in by_normalized_en:
            by_normalized_en[key] = japanese_name

    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    titles = {
        item["source_title"]
        for item in candidates.get("candidates", [])
        if item.get("source_title")
    }

    themes_text = THEMES_PATH.read_text(encoding="utf-8")
    titles.update(re.findall(r'source_title="([^"]+)"', themes_text))

    mapping = {}
    unmatched = []

    for title in sorted(titles):
        japanese_name = by_normalized_en.get(normalize(title))

        if japanese_name:
            mapping[title] = japanese_name
        else:
            unmatched.append(title)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "source": "Yu-Gi-Oh! Neuron registered categories",
                "names": mapping,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    UNMATCHED.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "unmatched_count": len(unmatched),
                "titles": unmatched,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"Yugipedia titles: {len(titles)}")
    print(f"Matched Japanese names: {len(mapping)}")
    print(f"Unmatched titles: {len(unmatched)}")
    print(f"Saved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        sys.exit(1)