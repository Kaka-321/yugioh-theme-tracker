# -*- coding: utf-8 -*-
"""Konami 公式「手札誘発まとめ」デッキから「相手が打てる妨害」データを生成する。

手順:
1. python crawler/fetch_opp_disruptors.py
   → Konami デッキ (cgid=4a187faf6971e83b722e374c84eb5d55 dno=29) の主デッキ/サイドの
     全カードを抽出し、YGOPRODeck で passcode を解決、
     既存の外部カード取得パイプライン (fetch_external_card + ensure_descs) で
     日本語画像・日本語効果テキストを取得して
     data/decks/opp_disruptors.json を生成する。
   画像は assets/cards/external/<slug>_jp.png に保存され
   external_cache.json 経由で decklab_ext.json にも反映される
   （デッキ編集の全カード検索からも追加可能になる）。

シミュレーション分類 (sim):
  negate      対象カードに「無効」バッジ（灰色表示）
  destroy     対象カードを破壊 → 墓地へ移動
  banish_field 対象カードを除外ゾーンへ移動
  gy_banish   自分の墓地のカードを除外ゾーンへ移動
  note        盤面変化なし（相手ドロー・サーチ封じ等の記録のみ）

分類は効果文キーワード + OVERRIDE マップで判定。
"""
import html as html_mod
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

CRAWLER = Path(__file__).resolve().parent
sys.path.insert(0, str(CRAWLER))

from build_blue_eyes_deck import (  # noqa: E402
    ROOT,
    ensure_descs,
    fetch_external_card,
    load_cache,
    load_desc_cache,
)
from fetch_blue_eyes_cards import clean_ja_name  # noqa: E402

DECK_URL = (
    "https://www.db.yugioh-card.com/yugiohdb/member_deck.action"
    "?cgid=4a187faf6971e83b722e374c84eb5d55&dno=29&request_locale=ja"
)
KONAMI_CARD_URL = "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=2&cid={cid}&request_locale={loc}"
UPDECK_HOST = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
OUT_PATH = ROOT / "data" / "decks" / "opp_disruptors.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}

ROW_PAT = re.compile(r'<td class="row_num">\s*(\d+)\s*</td>.*?cid=(\d+)', re.S)
EN_NAME_PAT = re.compile(r"<title>([^|<]+)\| Card Details")
JA_NAME_PAT = re.compile(r"<title>([^|<]+)\|")

# 分類の上書き（en 名 → (sim, note)）
OVERRIDE = {
    "Nibiru, the Primal Being": ("clear_field", "自分のモンスター全てを墓地へ送る（全体破壊）"),
    "Ghost Reaper & Winter Cherries": ("note", "相手EXデッキから同名カードを除外（盤面再現不可のため記録のみ）"),
    "Artifact Lancea": ("note", "このターン、墓地から除外できない（制約として記録）"),
    "Dimension Shifter": ("note", "このターン、墓地に行くカードは除外される（制約として記録）"),
    "Chaos Hunter": ("note", "相手はモンスターを除外できなくなる（制約として記録）"),
    "Retaliating \"C\"": ("negate", "対象にしたカードに「無効」表示"),
    "PSY-Framegear Gamma": ("destroy", "対象を破壊して墓地へ（無効化も伴う）"),
    # 盤面に置くタイプ（自分のフィールドに特殊召喚して使う妨害）
    "Bahalutiya, the Grand Radiance": ("summon", "相手フィールドに配置（アドバンス召喚で妨害の土台にする）"),
    "Primite Imperial Dragon": ("summon", "相手フィールドに配置（通常召喚）"),
    "The Abyss Dragon Swordsoul": ("summon", "相手フィールドに配置（幻竜族の効果で特殊召喚）"),
    "Theia, the Primal Being": ("summon", "相手フィールドに配置（リンク召喚）"),
    "Phantom Dragon": ("summon", "相手フィールドに配置（相手の特殊召喚に応じて特殊召喚）"),
    "Hop Ear Squadron": ("summon", "相手フィールドに配置（トークンを特殊召喚する誘発）"),
    "Kewl Tune Clip": ("summon", "相手フィールドに配置（シンクロ補助の誘発）"),
    "Gagaga Girl - Cell Phone Subtraction": ("summon", "相手フィールドに配置（EXデッキ誘発）"),
}


def http_get(url, timeout=50):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def deck_cids(page):
    """デッキページから (cid, row_num) を文書順で取り出す。"""
    out = []
    for m in ROW_PAT.finditer(page):
        cid = m.group(2)
        if not out or out[-1][0] != cid:
            out.append((cid, int(m.group(1))))
    seen = set()
    uniq = []
    for cid, rn in out:
        if cid in seen:
            continue
        seen.add(cid)
        uniq.append(cid)
    return uniq


def konami_en_name(cid):
    try:
        page = http_get(KONAMI_CARD_URL.format(cid=cid, loc="en"), timeout=40)
        m = EN_NAME_PAT.search(page)
        if m:
            en = html_mod.unescape(m.group(1)).strip()
            return en.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'").replace("&#248;", "ø") or None
    except Exception:
        return None
    return None


def konami_ja_name(cid):
    try:
        page = http_get(KONAMI_CARD_URL.format(cid=cid, loc="ja"), timeout=40)
        m = JA_NAME_PAT.search(page)
        if m:
            ja = html_mod.unescape(m.group(1)).strip()
            return ja or None
    except Exception:
        return None
    return None


def updeck_id(en_name):
    try:
        url = UPDECK_HOST + "?name=" + urllib.parse.quote(en_name)
        with urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "yugioh-theme-tracker/1.0"}), timeout=30
        ) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        rows = data.get("data") or []
        if rows:
            return rows[0].get("id")
    except Exception:
        pass
    return None


def _clean(text):
    if not text:
        return None
    text = re.sub(r"\[.*?\]", "", text)  # wikitext links
    text = html_mod.unescape(text)
    return text.strip() or None


def classify(ja_text, en_name):
    for ov_en, ov in OVERRIDE.items():
        if ov_en.lower() == (en_name or "").lower():
            return ov
    t = (ja_text or "").replace("\n", "")
    if not t:
        return "note", "（効果文未取得—過不足があれば要調整）"
    has_destroy = "破壊" in t
    has_negate = ("無効" in t) or ("無効化" in t)
    has_banish = "除外" in t
    gy_target_banish = bool(re.search(r"墓地の(カード|モンスター)(１|1)?(枚|体)?を?(選択|対象)?...?.{0,30}除外", t)) and has_banish
    if has_destroy and has_negate:
        return "destroy", "対象にしたカードを墓地へ破壊（移動）。効果は無効化も伴う"
    if has_destroy:
        return "destroy", "対象にしたカードを墓地へ破壊（移動）"
    if has_negate:
        return "negate", "対象にしたカードに「無効」表示"
    if gy_target_banish:
        return "gy_banish", "対象にした墓地のカードを除外ゾーンへ移動"
    if has_banish:
        return "banish_field", "対象にしたカードを除外ゾーンへ移動"
    if "ドロー" in t or "引き" in t:
        return "note", "ドロー効果の記録（盤面変化なし）"
    if "発動できない" in t or "禁止" in t or "封じ" in t:
        return "note", "制約として記録（盤面変化なし）"
    return "note", "記録として残す（盤面変化なし）"


def main():
    page = http_get(DECK_URL)
    cids = deck_cids(page)
    print(f"deck cards: {len(cids)}")

    rows = []
    for i, cid in enumerate(cids, 1):
        en = konami_en_name(cid)
        if not en:
            print(f"[{i}/{len(cids)}] cid={cid} en name NOT FOUND — skip")
            continue
        pid = updeck_id(en)
        rows.append({"cid": cid, "en": en, "ja": konami_ja_name(cid) or en, "id": pid})
        print(f"[{i}/{len(cids)}] {en} -> {pid}")
        time.sleep(0.25)

    en_list = [r["en"] for r in rows]
    desc_cache = load_desc_cache()
    ensure_descs(en_list, desc_cache)

    ext_cache = load_cache()
    for i, r in enumerate(rows, 1):
        en = r["en"]
        print(f"[ext {i}/{len(rows)}] {en}")
        fetch_external_card(en)
        time.sleep(0.2)
        if r["id"]:
            meta = ext_cache.setdefault(en, {"en": en, "jp": en, "slug": None})
            meta["card_id"] = r["id"]
    from build_blue_eyes_deck import save_cache  # late to avoid circular import noise
    save_cache(ext_cache)

    cards = []
    seen_ja = set()
    for i, r in enumerate(rows, 1):
        en = r["en"]
        meta = ext_cache.get(en) or {}
        d = desc_cache.get(en) or {}
        ja = r.get("ja") or clean_ja_name(meta.get("jp")) or en
        if not meta.get("image_path"):
            for slug_guess in (meta.get("slug"), re.sub(r"[^a-z0-9]+", "-", en.lower()).strip("-")):
                if slug_guess and (ROOT / f"assets/cards/external/{slug_guess}_jp.png").exists():
                    meta["image_path"] = f"assets/cards/external/{slug_guess}_jp.png"
                    break
        sim, note = classify(d.get("ja_text"), en)
        if ja in seen_ja:
            print(f"  dup: {ja} — skip")
            continue
        seen_ja.add(ja)
        cards.append(
            {
                "card_id": r["id"],
                "slug": None if r["id"] else (meta.get("slug") or None),
                "name": ja,
                "en_name": en,
                "image_path": meta.get("image_path"),
                "desc": d.get("ja_text") or None,
                "types": d.get("types") or None,
                "external": True,
                "sim": sim,
                "sim_note": note,
                "src": "opp_disruptors",
            }
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps({"cards": cards}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    n_by = {}
    for c in cards:
        n_by[c["sim"]] = n_by.get(c["sim"], 0) + 1
    print(f"opp_disruptors.json: {len(cards)} cards, sims: {n_by}, no image: "
          + str([c["en_name"] for c in cards if not c["image_path"]]))


if __name__ == "__main__":
    main()
