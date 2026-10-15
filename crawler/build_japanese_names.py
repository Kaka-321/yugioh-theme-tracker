import csv
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEURON_CSV = ROOT / "data" / "internal" / "neuron_categories.csv"
CANDIDATES = ROOT / "data" / "internal" / "theme_candidates.json"
THEMES_PATH = ROOT / "crawler" / "themes.py"
MANUAL_NAMES = ROOT / "data" / "meta" / "japanese_names_manual.json"
OUTPUT = ROOT / "data" / "meta" / "japanese_names.json"
UNMATCHED = ROOT / "data" / "internal" / "japanese_names_unmatched.json"

FUZZY_THRESHOLD = 0.82


def normalize(value):
    value = unicodedata.normalize("NFKC", value)
    value = value.lower()
    value = value.replace("·", "")
    value = value.replace("・", "")
    value = value.replace("＠", "")
    value = value.replace("@", "")
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def similarity(left, right):
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def main():
    with NEURON_CSV.open(encoding="utf-8-sig", newline="") as file:
        neuron_rows = list(csv.DictReader(file))

    neuron_entries = []
    for row in neuron_rows:
        english_name = (row.get("name_en") or "").strip()
        japanese_name = (row.get("name_ja") or "").strip()

        if english_name and japanese_name:
            neuron_entries.append((english_name, japanese_name))

    exact_by_key = {
        normalize(english_name): japanese_name
        for english_name, japanese_name in neuron_entries
        if normalize(english_name)
    }

    candidates = load_json(CANDIDATES, {})
    themes_text = THEMES_PATH.read_text(encoding="utf-8")

    titles = {
        item["source_title"]
        for item in candidates.get("candidates", [])
        if item.get("source_title")
    }
    titles.update(re.findall(r'source_title="([^"]+)"', themes_text))

    manual_data = load_json(MANUAL_NAMES, {})
    manual_names = manual_data.get("names", {})

    mapping = {}
    unmatched = []

    for title in sorted(titles):
        if title in manual_names:
            mapping[title] = manual_names[title]
            continue

        key = normalize(title)

        if key in exact_by_key:
            mapping[title] = exact_by_key[key]
            continue

        best_name = None
        best_score = 0.0

        for english_name, japanese_name in neuron_entries:
            score = similarity(key, normalize(english_name))
            if score > best_score:
                best_name = japanese_name
                best_score = score

        if best_name and best_score >= FUZZY_THRESHOLD:
            mapping[title] = best_name
        else:
            unmatched.append(title)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "source": "Yu-Gi-Oh! Neuron registered categories",
                "matching": {
                    "method": "manual, exact, fuzzy",
                    "fuzzy_threshold": FUZZY_THRESHOLD,
                },
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
    print(f"Manual names: {len(manual_names)}")
    print(f"Matched Japanese names: {len(mapping)}")
    print(f"Unmatched titles: {len(unmatched)}")
    print(f"Saved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        sys.exit(1)