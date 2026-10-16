#!/usr/bin/env python3
import json
import os
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

    save_json(BLUE_EYES_FILE, blue_eyes)
    print(f"added={len(new_cards)} total_cards={len(blue_eyes['cards'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
