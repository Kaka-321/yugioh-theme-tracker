# -*- coding: utf-8 -*-
"""デッキLab の検索追加カードを静的化する。

手順:
1. サイト（GitHub Pages）の デッキLab → 手動操作 → デッキ編集パネルの
   🧾書き出し ボタンで JSON をコピーし、 crawler/decklab_pending.json に保存する。
   例: {"theme":"red-dragon-archfiend","cards":[{"id":40366667,"en":"Dominus Impulse"}]}
2. python crawler/fetch_decklab_cards.py
   → 外部カード画像を assets/cards/external/ に取得し、
     external_cache.json / desc_cache.json を更新して
     data/decks/decklab_ext.json を再構築する。
3. git add して push すると GitHub Pages に反映。
   ブラウザは起動時に decklab_ext.json を読み込み、キャッシュの代わりに
   日本語画像・日本語テキストで復元される。

すでに external_cache.json / desc_cache.json にある外部カード
（blue-eyes 流れで取得済みのもの）もこのファイル経由で配信される。
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRAWLER = Path(__file__).resolve().parent
sys.path.insert(0, str(CRAWLER))

from fetch_blue_eyes_cards import clean_ja_name  # noqa: E402

from build_blue_eyes_deck import (  # noqa: E402
    ROOT as BG_ROOT,
    _box_param,
    _parse_box,
    ensure_descs,
    fetch_card_wikitext,
    fetch_external_card,
    load_cache,
    load_desc_cache,
    save_cache,
)

UPDECK_HOST = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
UA = {"User-Agent": "yugioh-theme-tracker crawler (github.com/Kaka-321)"}
PENDING_PATH = CRAWLER / "decklab_pending.json"
OUT_PATH = BG_ROOT / "data" / "decks" / "decklab_ext.json"


def updeck_id(en_name):
    """EN名から YGOPRODeck の card id（Konami passcode）を得る。"""
    for param in ("name", "fname"):
        url = UPDECK_HOST + "?" + param + "=" + urllib.parse.quote(en_name)
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            rows = data.get("data") or []
            if rows:
                return rows[0].get("id")
        except Exception:
            time.sleep(0.8)
    return None


def passcode_from_wikitext(en_name):
    try:
        wt = fetch_card_wikitext(en_name)
        time.sleep(0.4)
        box = _parse_box(wt)
        raw = _box_param(box, "password")
        return int(raw) if raw and str(raw).strip().isdigit() else None
    except Exception:
        return None


def ja_name_from_wikitext(en_name):
    try:
        wt = fetch_card_wikitext(en_name)
        time.sleep(0.3)
        box = _parse_box(wt)
        return _box_param(box, "ja_name") or None
    except Exception:
        return None


def main():
    if not PENDING_PATH.exists():
        print("decklab_pending.json がありません。サイトの 🧾書き出し 結果を保存してから実行してください。")
        return
    try:
        pending = json.loads(PENDING_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print("decklab_pending.json 読込失敗:", e)
        return
    pend_rows = pending.get("cards") if isinstance(pending, dict) else pending
    pend_rows = pend_rows or []

    ext_cache = load_cache()
    desc_cache = load_desc_cache()

    # pending を先に registration（画像/日本語スキャン取得）
    known = {}
    for i, row in enumerate(pend_rows, 1):
        en = (row.get("en") or "").strip() if isinstance(row, dict) else str(row).strip()
        if not en or en in known:
            continue
        known[en] = row.get("id") if isinstance(row, dict) else None
        print(f"[pending {i}/{len(pend_rows)}] {en}")
        if en not in ext_cache:
            fetch_external_card(en)
            time.sleep(0.4)
    # desc（ja_text / スペック）
    ensure_descs(sorted(set(known.keys()) | set(ext_cache.keys())), desc_cache)

    # card_id を付与して external_cache.json へ書き戻す
    for en, pid in known.items():
        if pid:
            ext_cache.setdefault(en, {"en": en, "jp": en, "slug": None})
            ext_cache[en]["card_id"] = pid
            if isinstance(ext_cache[en], dict):
                ext_cache[en]["card_id"] = pid
    for en in ext_cache:
        meta = ext_cache[en]
        if isinstance(meta, dict) and not meta.get("card_id"):
            pid = updeck_id(en)
            if pid:
                meta["card_id"] = pid
                print(f"[id] {en} -> {pid} (ygoprodeck)")
            else:
                meta["card_id"] = None
    save_cache(ext_cache)

    # decklab_ext.json 再構築（外部カード全件を配信）
    cards = []
    for en in sorted(ext_cache):
        meta = ext_cache[en] or {}
        if not isinstance(meta, dict):
            continue
        d = desc_cache.get(en) or {}
        if (meta.get("jp") or en) == en:
            ja_alt = ja_name_from_wikitext(en)
            if ja_alt:
                meta["jp"] = ja_alt
                ext_cache[en]["jp"] = ja_alt
                save_cache(ext_cache)
        card_id = meta.get("card_id")
        img = meta.get("image_path")
        if not img:
            for slug_guess in (meta.get("slug"), re.sub(r"[^a-z0-9]+", "-", en.lower()).strip("-")):
                if not slug_guess:
                    continue
                cand = f"assets/cards/external/{slug_guess}_jp.png"
                if (ROOT / cand).exists():
                    img = cand
                    meta["image_path"] = cand
                    break
        pid = card_id if isinstance(card_id, int) else None
        card = {
            "card_id": pid,
            "slug": None if pid else (meta.get("slug") or re.sub(r"[^a-z0-9]+", "-", en.lower()).strip("-") or None),
            "name": clean_ja_name(meta.get("jp")) or en,
            "en_name": en,
            "image_path": img,
            "desc": d.get("ja_text") or None,
            "types": d.get("types") or None,
            "attribute": d.get("attribute") or None,
            "level": d.get("level") or None,
            "atk": d.get("atk") or None,
            "def": d.get("def") or None,
            "external": True,
        }
        cards.append(card)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps({"cards": cards}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    static_n = sum(1 for c in cards if str(c["image_path"] or "").startswith("assets/cards/external/"))
    print(f"decklab_ext.json: {len(cards)} cards (日本語画像 {static_n})")


if __name__ == "__main__":
    main()
