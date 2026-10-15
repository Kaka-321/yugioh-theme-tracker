import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from check_source import cache_path, fetch_page, read_cache, save_cache, fetch_related_cards
from themes import THEMES

import re

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


def clean_japanese_name(value):
    value = re.sub(
        r"<ref[^>]*>.*?</ref>",
        "",
        value,
        flags=re.IGNORECASE | re.DOTALL,
    )
    value = re.sub(r"<ref[^>]*/>", "", value, flags=re.IGNORECASE)

    value = re.sub(
        r"\{\{Ruby\|([^|}]+)\|[^}]*\}\}",
        r"\1",
        value,
        flags=re.IGNORECASE,
    )

    while "{{" in value and "}}" in value:
        cleaned = re.sub(r"\{\{[^{}]*\}\}", "", value)
        if cleaned == value:
            break
        value = cleaned

    value = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", value)
    value = value.replace("'", "")
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def extract_japanese_name(source):
    wikitext = source.get("wikitext", "")
    match = re.search(
        r"\|\s*ja_name[ \t]*=[ \t]*([^\n]+)",
        wikitext,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    japanese_name = clean_japanese_name(match.group(1))

    if not japanese_name:
        return None

    return japanese_name


def build_theme(theme, source):
    japanese_name = extract_japanese_name(source)

    result = {
        "schema_version": "1.0.0",
        "theme_id": theme.theme_id,
        "canonical_name": None,
        "canonical_name_en": None,
        "aliases": [],
        "source_mode": "api-metadata-and-manual",
        "source": {
            "provider": "Yugipedia",
            "title": source.get("title"),
            "url": source.get("url"),
        },
    }

    # Blue-Eyes に対応：関連カードの抽出結果を含める
    if theme.theme_id == "blue-eyes":
        result["canonical_name"] = source.get("wikitext", "")
        result["canonical_name_en"] = "Blue-Eyes"
        result["aliases"] = sorted(set(theme.aliases))
        return result
    
    # 他のテーマ：日本語名を抽出して設定
    result["canonical_name"] = japanese_name or theme.canonical_name
    result["canonical_name_en"] = theme.canonical_name
    result["aliases"] = sorted(set(theme.aliases))

    return result


def build_theme_ja_names(source):
    """Blue-Eyes の Wikitext から日本語名（各カード）を抽出して JSON 形式で返す。"""
    names = []
    
    # MediaWiki リンクパターン：[[Title|Label]]
    import re
    link_pattern = r'\[\[([^\]]+)\]\]'
    matches = re.findall(link_pattern, source.get("wikitext", ""))
    
    for match in matches:
        # カテゴリやファイルページ、アニメ/漫画リンクを除外
        if (match.startswith("Category:") or 
            match.startswith("File:") or 
            match.startswith("Special:") or
            "|" in match or
            match.startswith("User:") or
            any(pat in match.lower() for pat in ["anime", "manga", "arcv", "rush"])):
            continue
        
        # タイトルを正常化（スペース→アンダースコア）
        canonical = match.replace(" ", "_")
        
        names.append({
            "title": match,
            "canonical_title": canonical,
        })
    
    return sorted(names, key=lambda x: x["title"])


def update_theme(theme, now, started_at):
    target = THEMES_DIR / f"{theme.theme_id}.json"

    try:
        source, source_used = get_source(theme, now)
        
        # Blue-Eyes に関連カード抽出を追加
        related_cards = None
        if theme.theme_id == "blue-eyes":
            print(">>> Extracting related cards from Wikitext...")
            cards = fetch_related_cards(source)
            if cards:
                print(f"    Found {len(cards)} related card(s)")
                related_cards = cards
        
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

    site_themes = []

    for theme in THEMES:
        theme_file = THEMES_DIR / f"{theme.theme_id}.json"

        if theme_file.exists():
            theme_data = json.loads(theme_file.read_text(encoding="utf-8"))
            canonical_name = theme_data.get("canonical_name", theme.canonical_name)
        else:
            canonical_name = theme.canonical_name

        site_themes.append({
            "theme_id": theme.theme_id,
            "canonical_name": canonical_name,
            "canonical_name_en": theme.canonical_name,
        })

    write_json(ROOT / "site" / "themes.json", {
        "schema_version": "1.0.0",
        "themes": site_themes,
    })

    print("STATUS: saved public theme list")
    print("STATUS: saved internal execution report")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()