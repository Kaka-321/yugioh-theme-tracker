import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEMES_PATH = ROOT / "crawler" / "themes.py"

REQUIRED_FIELDS = {
    "Yugipediaページ名": "source_title",
    "テーマID": "theme_id",
    "日本語名": "canonical_name",
}


def run_gh(arguments):
    result = subprocess.run(
        ["gh", *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def parse_issue_body(body):
    fields = {}
    current_label = None

    for line in body.splitlines():
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            current_label = heading.group(1).strip()
            fields[current_label] = ""
            continue

        if current_label is not None:
            fields[current_label] += line + "\n"

    return {
        key: value.strip()
        for key, value in fields.items()
    }


def build_theme_entry(source_title, theme_id, canonical_name, aliases):
    alias_values = [
        alias.strip()
        for alias in aliases.split(",")
        if alias.strip()
    ]

    alias_lines = ",\n".join(
        f'        "{alias}"'
        for alias in alias_values
    )

    return f'''    Theme(
        theme_id="{theme_id}",
        canonical_name="{canonical_name}",
        aliases=(
{alias_lines}
        ),
        source_title="{source_title}",
        source_url="https://yugipedia.com/wiki/{source_title.replace(' ', '_')}",
    ),
'''


def main():
    issue_number = os.environ.get("ISSUE_NUMBER")
    if not issue_number or not issue_number.isdigit():
        raise ValueError("ISSUE_NUMBER is missing or invalid")

    issue_json = run_gh([
        "issue", "view", issue_number,
        "--repo", "Kaka-321/yugioh-theme-tracker",
        "--json", "title,body,author",
    ])

    issue = json.loads(issue_json)
    body = issue.get("body") or ""
    fields = parse_issue_body(body)

    values = {}
    for label, key in REQUIRED_FIELDS.items():
        value = fields.get(label, "")
        if not value:
            raise ValueError(f"Missing required field: {label}")
        values[key] = value

    source_title = values["source_title"]
    theme_id = values["theme_id"]
    canonical_name = values["canonical_name"]
    aliases = fields.get("別名", "")

    if not re.fullmatch(r"[a-z0-9-]+", theme_id):
        raise ValueError("theme_id must contain only lowercase letters, numbers, and hyphens")

    themes_text = THEMES_PATH.read_text(encoding="utf-8")

    if f'theme_id="{theme_id}"' in themes_text:
        raise ValueError(f"Theme already registered: {theme_id}")

    if f'source_title="{source_title}"' in themes_text:
        raise ValueError(f"Source page already registered: {source_title}")

    entry = build_theme_entry(source_title, theme_id, canonical_name, aliases)

    marker = "THEMES = ("
    if marker not in themes_text:
        raise ValueError("THEMES tuple not found")

    closing_index = themes_text.rfind(")")
    if closing_index == -1:
        raise ValueError("THEMES tuple closing parenthesis not found")

    updated = (
        themes_text[:closing_index].rstrip()
        + "\n"
        + entry
        + themes_text[closing_index:]
    )

    THEMES_PATH.write_text(updated, encoding="utf-8")

    print(f"Added theme: {theme_id}")
    print(f"Source title: {source_title}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        sys.exit(1)