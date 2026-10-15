import json
import sys
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from themes import Theme

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / ".cache"
CACHE_TTL = timedelta(days=30)

API_URL = "https://yugipedia.com/api.php"
USER_AGENT = (
    "YugiohThemeTracker/0.1 "
    "(contact: https://github.com/Kaka-321/yugioh-theme-tracker/issues)"
)


def cache_path(theme: Theme) -> Path:
    return CACHE_DIR / f"yugipedia-wikitext-v2-{theme.theme_id}.json"


def read_cache(theme: Theme, now: datetime):
    cache = cache_path(theme)

    if not cache.exists():
        return None

    try:
        cached = json.loads(cache.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(cached["fetched_at"])
        age = now - fetched_at

        if (
            timedelta(0) <= age < CACHE_TTL
            and isinstance(cached["title"], str)
            and isinstance(cached["url"], str)
            and isinstance(cached["wikitext"], str)
        ):
            return cached
    except (ValueError, KeyError, TypeError, OSError):
        pass

    return None


def fetch_page(theme: Theme):
    params = {
        "action": "parse",
        "format": "json",
        "formatversion": "2",
        "page": theme.source_title,
        "prop": "wikitext",
        "redirects": "1",
        "maxlag": "5",
    }

    request = Request(
        API_URL + "?" + urlencode(params),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if "error" in payload:
        raise ValueError(
            "API error: "
            + json.dumps(payload["error"], ensure_ascii=False)
        )

    title = payload.get("parse", {}).get("title")
    wikitext = payload.get("parse", {}).get("wikitext")

    if not isinstance(title, str) or not isinstance(wikitext, str):
        raise ValueError("Page wikitext is missing")

    url = "https://yugipedia.com/wiki/" + quote(title.replace(" ", "_"))

    return {
        "title": title,
        "url": url,
        "wikitext": wikitext,
    }


def save_cache(theme: Theme, value: dict) -> None:
    cache = cache_path(theme)
    cache.parent.mkdir(parents=True, exist_ok=True)

    temporary = cache.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(cache)


def fetch_related_cards(theme: dict) -> list[dict]:
    """Yugipedia から Blue-Eyes に関連するカード一覧を wikitext のリンクで抽出する。"""
    excluded_patterns = ["anime", "manga", "arcv", "rush"]

    def extract_card_links(wikitext_content: str) -> list[str]:
        """Wikitext からカードページへのリンクを抽出する。"""
        cards = []
        
        # MediaWiki リンクパターン：[[Title|Label]] 形式
        link_pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(link_pattern, wikitext_content)
        
        for match in matches:
            # カテゴリやファイルページを除外
            if match.startswith("Category:") or match.startswith("File:") or match.startswith("Special:"):
                continue
                
            # 内部リンク（「|」を含む）は除外
            if "|" in match:
                continue
                
            # ユーザーページを除外
            if match.startswith("User:"):
                continue
                    
            cards.append(match)
        return cards

    wikitext = theme.get("wikitext", "")
    
    card_titles = extract_card_links(wikitext)
    
    # 重複を除去し、一意なカードタイトルに整形
    unique_cards = []
    seen_titles = set()
    
    for title_ref in card_titles:
        # タイトルを正常化（スペース→アンダースコア、除外パターン）
        normalized = title_ref.replace(" ", "_").lower().strip()
        
        # アニメ/漫画・アニメ専用を除外
        if any(pat in normalized for pat in excluded_patterns):
            continue
        
        if normalized not in seen_titles:
            seen_titles.add(normalized)
            unique_cards.append({
                "title": title_ref,
                "normalized_title": normalized,
            })

    return unique_cards


def main():
    now = datetime.now(timezone.utc)
    
    # テスト用にダミーのキャッシュデータのみ読み込む
    theme_id = "blue-eyes"
    cache_key = f"yugipedia-wikitext-v2-{theme_id}.json"
    cache_file = CACHE_DIR / cache_key
    
    if cache_file.exists():
        print(f"CACHE HIT: {cache_file.name}")
        
        # キャッシュを dict に読み込む
        import json
        result = json.loads(cache_file.read_text(encoding="utf-8").strip())
        
        # 関連カードの抽出を試みる
        cards = fetch_related_cards(result)
        
        if cards:
            print(f"EXTRACTED: found {len(cards)} related card(s)")
            
            for card in cards[:5]:  # 最初の 5 つを表示
                print(f"  - {card['title']}")
        else:
            print("NO CARDS: no related cards found")
    else:
        print(f"CACHE MISS: fetching from API... (will save to {cache_file.name})")


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
        print("FAILED:", error, file=sys.stderr)
        sys.exit(1)