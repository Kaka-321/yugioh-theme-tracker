import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "themes" / "blue-eyes.json"


def sample_theme():
    return {
        "schema_version": "1.0.0",
        "theme_id": "blue-eyes",
        "canonical_name": "青眼",
        "aliases": ["ブルーアイズ", "Blue-Eyes"],
        "source_mode": "sample",
    }


def normalize_theme(raw):
    return {
        "schema_version": raw["schema_version"],
        "theme_id": raw["theme_id"].strip(),
        "canonical_name": raw["canonical_name"].strip(),
        "aliases": sorted({
            alias.strip()
            for alias in raw["aliases"]
            if alias.strip()
        }),
        "source_mode": raw["source_mode"],
    }


def main():
    current = normalize_theme(sample_theme())

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

