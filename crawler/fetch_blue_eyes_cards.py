#!/usr/bin/env python3
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "themes"
ASSETS_DIR = ROOT / "assets" / "cards"
YGOPRODECK_BASE = "https://db.ygoprodeck.com/api/v7"
YGOPRO_API = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
USER_AGENT = "YugiohThemeTracker/0.1 (https://github.com/Kaka-321/yugioh-theme-tracker)"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

BLUE_EYES_FILE = DATA_DIR / "blue-eyes.json"

YUGIPEDIA_API = "https://yugipedia.com/api.php"
JP_IMAGE_RE = re.compile(r"([A-Za-z0-9()._-]+-JP-[A-Za-z0-9._-]+\.png)")
JP_EXCLUDE = ("VG-", "-artwork", "-DuelLinks")


def clean_ja_name(text):
    text = re.sub(r"\{\{Ruby\|([^|}]+)\|[^}]+\}\}", r"\1", text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def fetch_card_wikitext(title):
    try:
        data = safe_request(YUGIPEDIA_API, params={
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "format": "json",
            "formatversion": "2",
        })
        return data.get("parse", {}).get("wikitext", "") or ""
    except Exception as e:
        print(f"WIKITEXT_FAIL {title}: {e}")
        return ""


def get_ja_name_from_wikitext(wikitext):
    m = re.search(r"\|\s*ja_name\s*=\s*(.*)", wikitext)
    if m:
        jp = clean_ja_name(m.group(1).split("\n")[0])
        if jp and 2 < len(jp) < 60:
            return jp
    m = re.search(r"\|\s*furigana\s*=\s*(.*)", wikitext)
    if m:
        jp = clean_ja_name(m.group(1).split("\n")[0])
        if jp and 1 < len(jp) < 80:
            return jp
    return None


YP_EXCLUDE = ("VG-", "-artwork", "-DuelLinks", "Anime", "-info.png")
JP_CARD_RE = re.compile(r"-J[PA]-")


def list_card_image_files(title):
    """カード名をプレフィックスにして、Yugipedia上の関連画像ファイルを列挙する。"""
    filepart = re.sub(r"[ '\x22,._!?()×-]", "", title)
    try:
        data = safe_request(YUGIPEDIA_API, params={
            "action": "query",
            "list": "allimages",
            "aiprefix": filepart,
            "aisort": "name",
            "ailimit": "100",
            "format": "json",
            "formatversion": "2",
        })
        return [item["name"] for item in data.get("query", {}).get("allimages", [])]
    except Exception as e:
        print(f"ALLIMAGES_FAIL {title}: {e}")
        return []


def get_jp_card_file(wikitext, card_name):
    """日本語OCGカードスキャン（-JP-/-JA-）を選ぶ。jp_setsの先頭セットを優先。"""
    files = list_card_image_files(card_name)
    jp_files = [
        f for f in files
        if JP_CARD_RE.search(f)
        and not any(x in f for x in YP_EXCLUDE)
        and not f.endswith("-OP.png")
    ]
    if not jp_files:
        return None
    m = re.search(r"\|\s*jp_sets\s*=\s*\n(.*?)(?:\n\|\s*[a-z_]+\s*=|\Z)", wikitext, re.S)
    if m:
        first = m.group(1).strip().splitlines()[0]
        code = first.split(";")[0].strip()
        matches = [f for f in jp_files if f"-{code}-" in f]
        if matches:
            return matches[0]
    return jp_files[0]


def resolve_file_url(filename):
    try:
        data = safe_request(YUGIPEDIA_API, params={
            "action": "query",
            "titles": f"File:{filename}",
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
            "formatversion": "2",
        })
        for page in data.get("query", {}).get("pages", []):
            infos = page.get("imageinfo") or []
            if infos:
                return infos[0].get("url")
    except Exception as e:
        print(f"FILEURL_FAIL {filename}: {e}")
    return None


def download_binary(url, dest):
    if dest.exists():
        return True
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"IMG_DL_FAIL {dest.name}: {e}")
        return False


JP_CHARS = re.compile(r"[\u3040-\u30FF\u4E00-\u9FFF\uFF66-\uFF9D]")


def is_japanese(text):
    return bool(text) and bool(JP_CHARS.search(text))


def complete_japanese_assets(theme, now):
    """日本語名の欠落補完と、日本語OCGカード画像への差し替えを行う。"""
    updated_names = 0
    updated_images = 0

    for card in theme.get("cards", []):
        if not isinstance(card, dict) or not card.get("name"):
            continue

        name = card["name"]
        # 英語名が日本語名欄に入っている旧データは欠落扱いにする
        need_name = not is_japanese(card.get("japanese_name"))
        need_jp_image = not re.search(r"_jp\.(png|jpg)$", card.get("image_path") or "")

        if not need_name and not need_jp_image:
            continue

        wikitext = fetch_card_wikitext(name)
        if not wikitext:
            time.sleep(0.6)
            continue

        if need_name:
            jp = get_ja_name_from_wikitext(wikitext)
            if jp:
                card["japanese_name"] = jp
                updated_names += 1
                print(f"JP_NAME {name} -> {jp}")
            else:
                print(f"JP_NAME_NOT_FOUND {name}")

        if need_jp_image and card.get("card_id"):
            filename = get_jp_card_file(wikitext, name)
            if filename:
                file_url = resolve_file_url(filename)
                if file_url:
                    ext = ".png" if filename.endswith(".png") else ".jpg"
                    dest = ASSETS_DIR / f"{card['card_id']}_jp{ext}"
                    if download_binary(file_url, dest) and dest.stat().st_size > 1024:
                        card["image_path"] = f"assets/cards/{card['card_id']}_jp{ext}"
                        updated_images += 1
                        print(f"JP_IMG {name} -> {dest.name}")
            else:
                print(f"JP_IMG_NOT_FOUND {name}")

        time.sleep(0.6)

    return updated_names, updated_images

def safe_request(url, params=None, timeout=30):
    query = f"?{urlencode(params)}" if params else ""
    full = f"{url}{query}"
    req = Request(full, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data)


def load_json(p):
    if p.exists():
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_json(p, data):
    tmp = p.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(p)

def normalize_card(card):
    card_id = card.get("id")
    if card_id is None:
        return None

    name = card.get("name")
    card_images = card.get("card_images") or []
    image_url = card_images[0].get("image_url") if card_images else None

    ygoprodeck_url = None
    try:
        ygoprodeck_url = f"https://ygoprodeck.com/card/{name.replace(' ', '-').replace('/', '-')}-{card_id}/" if name else None
    except Exception:
        ygoprodeck_url = None

    level = card.get("level")
    atk = card.get("atk")
    defv = card.get("def")
    if level is not None and isinstance(level, str):
        try:
            level = int(level)
        except ValueError:
            level = None
    if atk is not None and isinstance(atk, str):
        try:
            atk = int(atk)
        except ValueError:
            atk = None
    if defv is not None and isinstance(defv, str):
        try:
            defv = int(defv)
        except ValueError:
            defv = None

    return {
        "card_id": int(card_id) if not isinstance(card_id, int) else card_id,
        "name": name,
        "japanese_name": None,
        "type": card.get("type"),
        "attribute": card.get("attribute"),
        "race": card.get("race"),
        "level": level,
        "atk": atk,
        "def": defv,
        "image_path": f"assets/cards/{card_id}.jpg" if card_id else None,
        "image_url": image_url,
        "ygoprodeck_url": ygoprodeck_url,
        "first_seen_at": None,
    }

def download_image(url, dest):
    if not url or dest.exists():
        return
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
        dest.write_bytes(data)
        time.sleep(0.5)
    except Exception as e:
        print(f"IMAGE_DL_FAIL {dest.name}: {e}")


def get_japanese_name(card_name, card_id):
    try:
        from urllib.request import urlopen as _urlopen
        from urllib.parse import quote as _quote
        from urllib.request import Request as _req
        url = f"https://yugipedia.com/api.php?action=query&format=json&titles={_quote(card_name)}&prop=extracts&exintro=1&explaintext=1&redirects=1"
        req = _req(url, headers={"User-Agent": USER_AGENT})
        with _urlopen(req, timeout=20) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        pages = d.get("query", {}).get("pages", {})
        for k, v in pages.items():
            ext = v.get("extract", "")
            if not ext:
                continue
            for line in ext.splitlines():
                if "Japanese" in line and ":" in line:
                    val = line.split(":", 1)[1].strip()
                    if val and len(val) < 80:
                        return val
    except Exception:
        pass
    return None

def enrich_legacy_cards(theme, now):
    """card_id/image_path の無い既存カード行を YGOPRODeck で補完する。"""
    enriched = 0
    for card in theme.get("cards", []):
        if not isinstance(card, dict):
            continue
        if card.get("card_id") and card.get("image_path") and card.get("type"):
            continue

        name = card.get("name")
        if not name:
            continue

        try:
            data = safe_request(YGOPRO_API, params={"name": name})
            matches = data.get("data", []) if isinstance(data, dict) else []
        except Exception as e:
            print(f"ENRICH_FAIL name={name}: {e}")
            time.sleep(1.0)
            continue

        if not matches:
            print(f"ENRICH_NOT_FOUND name={name}")
            time.sleep(0.5)
            continue

        target = matches[0]
        detail = normalize_card(target) or {}
        card_id = detail.get("card_id")
        if not card_id:
            continue

        card["card_id"] = card_id
        for key in ("type", "attribute", "race", "level", "atk", "def"):
            if detail.get(key) is not None:
                card[key] = detail[key]
        if not card.get("ygoprodeck_url"):
            card["ygoprodeck_url"] = detail.get("ygoprodeck_url")

        dest = ASSETS_DIR / f"{card_id}.jpg"
        image_url = (target.get("card_images") or [{}])[0].get("image_url")
        download_image(image_url, dest)
        if dest.exists():
            card["image_path"] = f"assets/cards/{card_id}.jpg"
        else:
            card["image_path"] = None

        if not card.get("japanese_name") or len(card.get("japanese_name", "")) < 4:
            jp_api = (target.get("misc") or {}).get("jp_name")
            if jp_api:
                card["japanese_name"] = jp_api
            else:
                jp = get_japanese_name(name, card_id)
                if jp:
                    card["japanese_name"] = jp

        if not card.get("first_seen_at"):
            card["first_seen_at"] = now

        enriched += 1
        print(f"ENRICHED name={name} card_id={card_id}")
        time.sleep(0.5)

    return enriched


def main():
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        data = safe_request(YGOPRO_API, params={"archetype": "Blue-Eyes"})
        cards = data.get("data", []) if isinstance(data, dict) else []
    except Exception as e:
        print(f"YGOPRODECK_FETCH_FAIL: {e}")
        return 1

    blue_eyes = load_json(BLUE_EYES_FILE) or {}
    existing_cards = blue_eyes.get("cards", []) or []
    existing_ids = set()
    for c in existing_cards:
        cid = c.get("card_id")
        if cid is not None:
            existing_ids.add(int(cid))

    if "changes" not in blue_eyes or not isinstance(blue_eyes["changes"], list):
        blue_eyes["changes"] = []

    changes = []
    new_cards = []
    for card in cards:
        norm = normalize_card(card)
        if not norm:
            continue
        cid = norm["card_id"]
        if cid in existing_ids:
            continue
        dest = ASSETS_DIR / f"{cid}.jpg"
        download_image(norm.pop("image_url", None), dest)
        if not dest.exists():
            norm["image_path"] = None
        jp = get_japanese_name(norm["name"], cid)
        if jp:
            norm["japanese_name"] = jp
        else:
            norm["japanese_name"] = None
        norm["first_seen_at"] = now
        new_cards.append(norm)
        existing_ids.add(cid)
        changes.append({
            "card_id": cid,
            "name": norm["name"],
            "added_at": now,
        })
        time.sleep(0.3)

    blue_eyes["cards"] = existing_cards + new_cards
    blue_eyes["changes"].extend(changes)

    enriched = enrich_legacy_cards(blue_eyes, now)
    jp_names, jp_images = complete_japanese_assets(blue_eyes, now)

    save_json(BLUE_EYES_FILE, blue_eyes)
    print(
        f"added={len(new_cards)} enriched={enriched} "
        f"jp_names={jp_names} jp_images={jp_images} "
        f"total_cards={len(blue_eyes['cards'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
