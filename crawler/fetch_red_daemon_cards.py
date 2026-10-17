# -*- coding: utf-8 -*-
"""Red Dragon Archfiend (レッド・デーモン) テーマデータの取得スクリプト。

- data/themes/red-dragon-archfiend.json を完全カードデータ形式に更新する。
- 対象カード一覧はデッキLab構成 (crawler/build_red_daemon_deck.py) と同じもの。
"""

import time
from datetime import datetime, timezone
from urllib.parse import quote

from fetch_blue_eyes_cards import (
    DATA_DIR,
    ASSETS_DIR,
    YGOPRO_API,
    USER_AGENT,
    safe_request,
    load_json,
    save_json,
    normalize_card,
    download_image,
    get_japanese_name,
    complete_japanese_assets,
)

RED_FILE = DATA_DIR / "red-dragon-archfiend.json"

RED_DAEMON_CARD_IDS = [
    34761841,  # Crimson Resonator
    62991792,  # Soul Resonator
    40975574,  # Red Resonator
    97021916,  # Dark Resonator
    14886469,  # Red Sprinter
    72318602,  # Red Gardna
    45313993,  # Red Warg
    23008320,  # Resonator Call
    8559524,   # Resonator Command
    98173209,  # Crimson Gaia
    99398682,  # Crimson Call
    66141736,  # Red Rising Dragon
    76547525,  # Red Wyvern
    70902743,  # Red Dragon Archfiend
    87451661,  # Scarred Dragon Archfiend
    39765958,  # Hot Red Dragon Archfiend
    80666118,  # Scarlight Red Dragon Archfiend
    9753964,   # Hot Red Dragon Archfiend Abyss
    36857073,  # Hot Red Dragon Archfiend Bane
    62242678,  # Hot Red Dragon Archfiend King Calamity
    16172067,  # Tyrant Red Dragon Archfiend
    99585850,  # Red Supernova Dragon
    97489701,  # Red Nova Dragon
    21142671,  # Red Nova
]


def fetch_card_info(cid):
    return safe_request(YGOPRO_API, params={"id": cid})


def main():
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    existing = load_json(RED_FILE) or {}
    theme = {
        "schema_version": "1.0.0",
        "theme_id": "red-dragon-archfiend",
        "canonical_name": existing.get("canonical_name") or "レッド・デーモン",
        "canonical_name_en": existing.get("canonical_name_en") or "Red Dragon Archfiend",
        "aliases": existing.get("aliases") or [],
        "expansion": existing.get("expansion") or [],
        "image": existing.get("image"),
        "source": existing.get("source") or {
            "provider": "Yugipedia",
            "title": "Red Dragon Archfiend",
            "url": "https://yugipedia.com/wiki/Red_Dragon_Archfiend",
        },
        "source_mode": existing.get("source_mode") or "api-metadata-and-manual",
        "cards": [],
        "changes": [],
    }

    for cid in RED_DAEMON_CARD_IDS:
        try:
            data = fetch_card_info(cid)
            raw = (data.get("data") or [])[0]
        except Exception as e:
            print(f"FETCH_FAIL {cid}: {e}")
            continue
        norm = normalize_card(raw)
        if not norm:
            continue
        image_url = norm.pop("image_url", None)
        dest = ASSETS_DIR / f"{norm['card_id']}.jpg"
        download_image(image_url, dest)
        if not dest.exists():
            norm["image_path"] = None
        jp = get_japanese_name(norm["name"], cid)
        norm["japanese_name"] = jp
        norm["first_seen_at"] = now
        theme["cards"].append(norm)
        theme["changes"].append({"card_id": cid, "name": norm["name"], "added_at": now})
        print(f"OK {cid} {norm['name']}")
        time.sleep(0.3)

    if len(theme["cards"]) != len(RED_DAEMON_CARD_IDS):
        missing = len(RED_DAEMON_CARD_IDS) - len(theme["cards"])
        print(f"WARN: {missing} card(s) missing")
        return 1

    saved = complete_japanese_assets(theme, now)
    save_json(RED_FILE, theme)
    print(f"saved data/themes/red-dragon-archfiend.json cards={len(theme['cards'])} jp={saved}")


if __name__ == "__main__":
    main()
