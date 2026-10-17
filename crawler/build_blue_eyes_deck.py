# -*- coding: utf-8 -*-
"""Blue-Eyes テンプレートデッキ + 展開ルート + 妨害対応データのビルドスクリプト。

- data/decks/blue-eyes.json を生成する。
- テーマ外カード（マエルト/魔導書など）と妨害カードの日本語OCGスキャン画像を
  assets/cards/external/ に取得して参照する。
- 生成されるルート・妨害対応はドラフトであり、効果テキストの精査は未実施。
"""

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_blue_eyes_cards import (
    ROOT,
    USER_AGENT,
    fetch_card_wikitext,
    list_card_image_files,
    get_ja_name_from_wikitext,
    get_jp_card_file,
    resolve_file_url,
    download_binary,
)

DECK_DIR = ROOT / "data" / "decks"
EXT_DIR = ROOT / "assets" / "cards" / "external"
CACHE_PATH = DECK_DIR / "external_cache.json"

# (Yugipedia English page title, 参考用の読み) — 正式日本語名はAPIから取得する
EXTERNAL_TITLES = [
    'The Melody of Awakening Dragon',
    'Dragon Shrine',
    'Maxx "C"',
    'Ash Blossom & Joyous Spring',
    'Effect Veiler',
    'Infinite Impermanence',
    'Called by the Grave',
    'Hieratic Seal of the Sun Dragon Overlord',
    'Droll & Lock Bird',
]

DISRUPTION_TITLES = [
    'Maxx "C"',
    'Ash Blossom & Joyous Spring',
    'Effect Veiler',
    'Infinite Impermanence',
    'Called by the Grave',
    'Droll & Lock Bird',
]


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "card"


def load_cache():
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def fetch_external_card(title):
    """テーマ外カードの日本語スキャン画像を取得し、情報を返す。"""
    slug_ = slug(title)
    image_path = f"assets/cards/external/{slug_}_jp.png"
    if (ROOT / image_path).exists():
        cached = load_cache().get(title)
        if not cached:
            cached = {"en": title, "jp": title, "slug": slug_}
        if not cached.get("image_path"):
            cached["image_path"] = image_path
            cache_ = load_cache()
            cache_[title] = cached
            save_cache(cache_)
        return cached
    wikitext = fetch_card_wikitext(title)
    time.sleep(0.6)
    ja = get_ja_name_from_wikitext(wikitext) or title
    prefix_source = title.replace('&', '')
    filename = None
    for files_source in (prefix_source, title):
        files = list_card_image_files(files_source)
        jp_files = [
            f for f in files
            if re.search(r"-J[PA]-", f) and 'VG-' not in f and '-artwork' not in f
            and '-DuelLinks' not in f and 'Anime' not in f and not f.endswith('-OP.png')
        ]
        if jp_files:
            filename = jp_files[0]
            break
        time.sleep(0.3)
    if filename:
        url = resolve_file_url(filename)
        if url:
            EXT_DIR.mkdir(parents=True, exist_ok=True)
            download_binary(url, ROOT / image_path)
    if not filename:
        if (ROOT / image_path).exists():
            print(f"EXT_REUSE_FILE {title}")
        else:
            print(f"EXT_NOFILE {title}")
            image_path = None
    info = {"en": title, "jp": ja, "slug": slug_, "image_path": image_path}
    cache = load_cache()
    cache[title] = info
    save_cache(cache)
    return info


def main():
    cache = load_cache()
    need = [t for t in EXTERNAL_TITLES if t not in cache]
    for i, title in enumerate(need, 1):
        print(f"[{i}/{len(need)}] fetching external card: {title}")
        fetch_external_card(title)
        time.sleep(0.3)

    cache = load_cache()
    for t in EXTERNAL_TITLES:
        ent = cache.get(t)
        if not ent:
            continue
        expected = f"assets/cards/external/{slug(t)}_jp.png"
        if not ent.get("image_path") and (ROOT / expected).exists():
            ent["image_path"] = expected
            save_cache(cache)
    missing = [t for t in EXTERNAL_TITLES if t not in cache]
    if missing:
        print(f"EXTERNAL_FAIL {missing}")
        return 1

    ext = cache
    ext_img = {t: (ext[t] or {}).get("image_path") for t in EXTERNAL_TITLES}
    ext_jp = {t: (ext[t] or {}).get("jp") for t in EXTERNAL_TITLES}

    # ---- テーマカード参照用マップ ----
    theme_path = ROOT / "data" / "themes" / "blue-eyes.json"
    theme = json.loads(theme_path.read_text(encoding="utf-8"))
    by_id = {}
    for card in theme.get("cards", []):
        if isinstance(card, dict) and card.get("card_id") is not None:
            by_id[str(card["card_id"])] = card

    def th(cid):
        card = by_id.get(str(cid))
        if card is None:
            raise KeyError(f"theme card missing: {cid}")
        return {
            "card_id": card["card_id"],
            "name": card["japanese_name"] or card["name"],
            "image_path": card["image_path"],
            "external": False,
        }

    def ex(title):
        return {
            "slug": ext[title]["slug"],
            "name": ext_jp[title],
            "image_path": ext_img[title],
            "external": True,
        }

    # ---- デッキ構成一覧 ----
    main_deck = [
        ("88241506", 3, "始動"),   # 青き眼の乙女
        ("36734924", 3, "始動"),   # 青き眼の巫女
        ("45644898", 2, "始動"),   # 青き眼の祭司
        ("8240199", 2, "補助"),    # 青き眼の賢士
        ("72855441", 1, "補助"),   # 青き眼の護人
        ("34627841", 2, "展開"),   # 正義の味方 カイバーマン
        ("71039903", 3, "白来"),   # 太古の白石
        ("79814787", 3, "白来"),   # 伝説の白石
        ("89631139", 3, "青山白龍"),# 青眼の白龍
        ("38517737", 1, "青山白龍"),# 青眼の亜白龍
        ("45467446", 1, "青山白龍"),# 白き霊龍
        ("30397786", 1, "青山白龍"),# 白き幻獣－青眼の白龍
        (None, 3, "青山白龍", 'The Melody of Awakening Dragon'),
        (None, 1, "補助", 'Dragon Shrine'),
        (None, 3, "妨害", 'Maxx "C"'),
        (None, 3, "妨害", 'Ash Blossom & Joyous Spring'),
        (None, 2, "妨害", 'Effect Veiler'),
        (None, 1, "妨害", 'Infinite Impermanence'),
        (None, 2, "妨害", 'Called by the Grave'),
    ]
    extra_deck = [
        ("23995346", 2, "青山"),   # 青眼の究極竜
        ("56532353", 1, "青山"),   # 真青眼の究極竜
        ("43228023", 1, "青山"),   # 青眼の究極亜竜
        ("62873545", 1, "青山"),   # 究極竜騎士
        ("2129638", 1, "青山"),    # 青眼の双爆裂龍
        ("11443677", 1, "青山"),   # ブルーアイズ・タイラント・ドラゴン
        ("59822133", 2, "青山"),   # 青眼の精霊龍
        ("53347303", 1, "青山"),   # 青眼の光龍
        ("89604813", 1, "青山"),   # 青眼の究極霊竜
        ("22804410", 1, "青山"),   # ディープアイズ・ホワイト・ドラゴン
        (None, 1, "汎用", 'Hieratic Seal of the Sun Dragon Overlord'),
    ]

    def build_entries(raw):
        entries = []
        for item in raw:
            if len(item) == 4 and item[0] is None:
                _, count, role, title = item
                ent = ex(title)
            else:
                cid, count, role = item
                ent = th(cid)
            entries.append(dict(ent, count=int(count), role=role))
        return entries

    main_entries = build_entries(main_deck)
    extra_entries = build_entries(extra_deck)

    def entry_info(e):
        return {
            "card_id": e.get("card_id"),
            "slug": e.get("slug"),
            "name": e["name"],
            "image_path": e["image_path"],
            "external": bool(e["external"]),
            "count": e["count"],
            "role": e["role"],
        }

    # ---- 展開ルート（盤面スナップショット付き） ----
    def card(cid, label=None):
        c = th(cid)
        if label:
            c = dict(c, label=label)
        return c

    def cardx(title, label=None):
        c = ex(title)
        if label:
            c = dict(c, label=label)
        return c

    def board(monsters=None, spells=None, hand=None, gy=None, banish=None, extra=None):
        def pad(lst):
            lst = list(lst or [])
            return lst + [None] * max(0, 5 - len(lst))
        return {
            "monsters": pad(monsters),
            "spells": pad(spells),
            "hand": list(hand or []),
            "gy": list(gy or []),
            "banish": list(banish or []),
            "extra": list(extra or []),
        }

    routes = [
        {
            "id": "r1",
            "name": "青き眼の乙女始動（基本ルート）",
            "summary": "乙女1枚から賢士・白石を絡めて精霊龍＋究極竜の盤面を目指す王道ルート。",
            "steps": [
                {"card": card("88241506"), "act": "召喚/特殊召喚", "note": "青き眼の乙女を召喚（条件を満たせば特殊召喚も可）。", "events": ["ss"],
                 "board": board(monsters=[card("88241506")], hand=[card("89631139")])},
                {"card": card("88241506"), "act": "効果", "note": "乙女の効果で手札の青眼の白龍を墓地へ送り、青き眼の賢士を特殊召喚。", "events": ["field_eff", "gy_eff", "ss"],
                 "board": board(monsters=[card("88241506"), card("8240199")], gy=[card("89631139")])},
                {"card": card("8240199"), "act": "効果", "note": "賢士の効果で伝説の白石をサーチ。", "events": ["search"],
                 "board": board(monsters=[card("88241506"), card("8240199")], hand=[card("79814787")], gy=[card("89631139")])},
                {"card": card("79814787"), "act": "効果", "note": "手札の伝説の白石を墓地へ送り、その効果で青眼の白龍を特殊召喚。", "events": ["gy_eff", "ss"],
                 "board": board(monsters=[card("88241506"), card("8240199"), card("89631139")], gy=[card("89631139"), card("79814787")], hand=[])},
                {"card": card("59822133"), "act": "シンクロ", "note": "賢士（Lv1）＋青眼の白龍（Lv8）で、青眼の精霊龍をシンクロ召喚。", "events": ["synchro"],
                 "board": board(monsters=[card("88241506"), card("59822133")], gy=[card("89631139"), card("79814787"), card("8240199")], extra=[card("59822133")])},
                {"card": card("71039903", "墓地から再展開"), "act": "効果", "note": "墓地の白石効果で4枚目の白石または青眼のパーツを特殊召喚し、手札を回復。", "events": ["gy_eff", "ss"],
                 "board": board(monsters=[card("88241506"), card("59822133"), card("71039903", "墓地から再展開")], gy=[card("89631139"), card("79814787"), card("8240199")], extra=[card("59822133")])},
                {"card": card("23995346"), "act": "融合", "note": "究極融合：墓地・手札の青眼の白龍たちを素材に、青眼の究極竜を融合召喚。", "events": ["fusion", "spell"],
                 "board": board(monsters=[card("88241506"), card("59822133")], spells=[card("71143015")], gy=[card("89631139"), card("79814787"), card("8240199")], extra=[card("23995346", "融合召喚")], banish=[])},
                {"act": "盤面確定", "note": "終盤：青眼の精霊龍＋青眼の究極竜＋乙女。打点・妨害ともに厚い盤面。",
                 "board": board(monsters=[card("88241506"), card("59822133")], gy=[card("89631139"), card("79814787"), card("8240199")], extra=[card("23995346", "融合召喚")])},
            ],
        },
        {
            "id": "r2",
            "name": "青き眼の祭司始動（白石ループ）",
            "summary": "祭司1枚から白石を回し、除外系の亜白龍や究極竜で押すルート。",
            "steps": [
                {"card": card("45644898"), "act": "召喚/特殊召喚", "note": "青き眼の祭司を召喚（または効果で特殊召喚）。", "events": ["ss"],
                 "board": board(monsters=[card("45644898")], hand=[card("71039903"), card("89631139")])},
                {"card": card("45644898"), "act": "効果", "note": "祭司の効果で太古の白石をサーチ（または墓地へ送って展開）。", "events": ["search"],
                 "board": board(monsters=[card("45644898")], hand=[card("71039903")], gy=[card("89631139")])},
                {"card": card("71039903"), "act": "効果", "note": "太古の白石を墓地へ送り、効果で白石または青き眼を特殊召喚（ループを回す）。", "events": ["gy_eff", "ss"],
                 "board": board(monsters=[card("45644898"), card("79814787", "白石ループ")], gy=[card("89631139"), card("71039903")])},
                {"card": card("38517737"), "act": "特殊召喚", "note": "墓地の青眼の白龍を除外して、青眼の亜白龍を特殊召喚。", "events": ["ss"],
                 "board": board(monsters=[card("45644898"), card("79814787", "白石ループ"), card("38517737")], banish=[card("89631139", "除外")], gy=[card("71039903")])},
                {"card": card("79814787"), "act": "効果", "note": "墓地の白石効果でサーチし、手札を補強。", "events": ["gy_eff", "search"],
                 "board": board(monsters=[card("45644898"), card("79814787", "白石ループ"), card("38517737")], hand=[card("71143015", "究極融合")], banish=[card("89631139", "除外")], gy=[card("71039903")])},
                {"card": card("62873545"), "act": "融合", "note": "究極融合：手札・墓地の青眼の白龍を融合素材に、究極竜系（究極竜騎士／究極亜竜）を融合召喚。", "events": ["fusion", "spell"],
                 "board": board(monsters=[card("45644898"), card("79814787", "白石ループ")], spells=[card("71143015")], extra=[card("62873545", "fusion")], banish=[card("89631139", "除外")], gy=[card("71039903")])},
                {"act": "盤面確定", "note": "終盤：青眼の亜白龍＋究極竜系＋余剰の手札。妨害に強い盤面。",
                 "board": board(monsters=[card("38517737"), card("62873545")], extra=[card("62873545", "fusion")], banish=[card("89631139", "除外")], gy=[card("71039903")])},
            ],
        },
        {
            "id": "r3",
            "name": "ドラゴン覚醒の旋律始動（SS少なめ）",
            "summary": "旋律＋霊廟で墓地を整え、最小限の特殊召喚で究極竜を立てる安定ルート。",
            "steps": [
                {"card": cardx('The Melody of Awakening Dragon'), "act": "魔法発動", "note": "ドラゴン・目覚めの旋律：手札の竜を墓地へ送り、青眼の白龍と青き眼のパーツをサーチ。", "events": ["spell", "search"],
                 "board": board(hand=[card("89631139"), card("71039903")], gy=[cardx('The Melody of Awakening Dragon', "発動済み")])},
                {"card": cardx('Dragon Shrine'), "act": "魔法発動", "note": "竜の霊廟：手札の白石を墓地へ送り、墓地で効果を仕込む。", "events": ["spell", "gy_eff"],
                 "board": board(hand=[card("79814787")], gy=[cardx('The Melody of Awakening Dragon', "発動済み"), cardx('Dragon Shrine', "発動済み")])},
                {"card": card("71039903", "墓地から特殊召喚"), "act": "墓地効果", "note": "墓地の太古の白石効果で白石を特殊召喚。", "events": ["gy_eff", "ss"],
                 "board": board(monsters=[card("71039903", "墓地から特殊召喚")], hand=[card("79814787")], gy=[cardx('The Melody of Awakening Dragon', "発動済み"), cardx('Dragon Shrine', "発動済み")])},
                {"card": card("59822133"), "act": "シンクロ", "note": "白石（Lv1）＋青眼の白龍（Lv8）で、青眼の精霊龍をシンクロ召喚。", "events": ["synchro"],
                 "board": board(monsters=[card("59822133")], gy=[cardx('The Melody of Awakening Dragon', "発動済み"), cardx('Dragon Shrine', "発動済み"), card("71039903"), card("89631139")], extra=[card("59822133")])},
                {"card": card("79814787"), "act": "墓地効果", "note": "墓地の伝説の白石効果でサーチし、手札を整える。", "events": ["gy_eff", "search"],
                 "board": board(monsters=[card("59822133")], hand=[card("71143015", "究極融合")], gy=[cardx('The Melody of Awakening Dragon', "発動済み"), cardx('Dragon Shrine', "発動済み"), card("71039903"), card("79814787")], extra=[card("59822133")])},
                {"card": card("23995346"), "act": "融合", "note": "究極融合：手札・墓地の青眼の白龍を融合素材に、青眼の究極竜を融合召喚。", "events": ["fusion", "spell"],
                 "board": board(monsters=[card("59822133")], spells=[card("71143015")], gy=[cardx('The Melody of Awakening Dragon', "発動済み"), cardx('Dragon Shrine', "発動済み"), card("71039903"), card("79814787"), card("89631139")], extra=[card("23995346", "fusion")])},
                {"act": "盤面確定", "note": "終盤：青眼の精霊龍＋青眼の究極竜。特殊召喚が少なく妨害に引かれにくい。",
                 "board": board(monsters=[card("59822133")], gy=[cardx('The Melody of Awakening Dragon', "発動済み"), cardx('Dragon Shrine', "発動済み"), card("71039903"), card("79814787"), card("89631139")], extra=[card("23995346", "fusion")])},
            ],
        },
        {
            "id": "r4",
            "name": "カイバーマン始動（サーチ最小）",
            "summary": "カイバーマン1枚から青眼の白龍へ直結。サーチが少なく、妨害への引きが浅い。",
            "steps": [
                {"card": card("34627841"), "act": "召喚", "note": "正義の味方 カイバーマンを通常召喚。", "events": [],
                 "board": board(monsters=[card("34627841")], hand=[card("89631139"), card("79814787")])},
                {"card": card("34627841"), "act": "効果", "note": "カイバーマンを生贄に捧げて、手札の青眼の白龍を特殊召喚。", "events": ["ss"],
                 "board": board(monsters=[card("89631139")], gy=[card("34627841")], hand=[card("79814787")])},
                {"card": card("79814787"), "act": "効果", "note": "白石の効果で展開を補助（サーチ＋白石特殊召喚）。", "events": ["gy_eff", "search", "ss"],
                 "board": board(monsters=[card("89631139"), card("71039903", "墓地から展開")], gy=[card("34627841"), card("79814787")], hand=[])},
                {"card": card("59822133"), "act": "シンクロ", "note": "白石（Lv1）＋青眼の白龍（Lv8）で、青眼の精霊龍をシンクロ召喚。", "events": ["synchro"],
                 "board": board(monsters=[card("59822133")], gy=[card("34627841"), card("79814787"), card("89631139"), card("71039903")], extra=[card("59822133")])},
                {"card": card("23995346"), "act": "融合", "note": "究極融合：墓地・手札の青眼の白龍を融合素材に、青眼の究極竜を融合召喚。", "events": ["fusion", "spell"],
                 "board": board(monsters=[card("59822133")], spells=[card("71143015")], gy=[card("34627841"), card("79814787"), card("89631139"), card("71039903")], extra=[card("23995346", "fusion")])},
                {"act": "盤面確定", "note": "終盤：青眼の精霊龍＋青眼の究極竜＋究極融合。打点、ドロー系の妨害にも引きが浅くなる。",
                 "board": board(monsters=[card("59822133")], spells=[card("71143015")], gy=[card("34627841"), card("79814787"), card("89631139"), card("71039903")], extra=[card("23995346", "fusion")])},
            ],
        },
    ]

    # ---- 妨害カード ----
    disruptions = [
        {
            "id": "d_g",
            "title": 'Maxx "C"',
            "jp": ext_jp['Maxx "C"'],
            "image_path": ext_img['Maxx "C"'],
            "effect": "自分の特殊召喚のたびに相手がドローする。SS数が多い展開は不利に。",
            "events": ["ss"],
            "handlers": [
                {"label": "このまま押し切る", "path": "continue", "note": "引き換え覚悟で打点で押す。終盤が厚く まだ余裕がある場合は有効。"},
                {"label": "SSを減らせるルートへ", "path": {"route": "r3", "from_step": 0}, "note": "旋律始動（r3）は特殊召喚が少なく、Gにドローを与えにくいのでルート変更が安全。"},
            ],
        },
        {
            "id": "d_ash",
            "title": 'Ash Blossom & Joyous Spring',
            "jp": ext_jp['Ash Blossom & Joyous Spring'],
            "image_path": ext_img['Ash Blossom & Joyous Spring'],
            "effect": "サーチ・墓地送り・EXからの特殊召喚を無効にする。",
            "events": ["search", "ss", "gy_eff"],
            "handlers": [
                {"label": "切断されたアクションを飛ばして続行", "path": "continue", "note": "無効にされた動作を飛ばして、残った手札で 最小限の盤面をつくる。"},
                {"label": "サーチの少ないルートへ", "path": {"route": "r4", "from_step": 0}, "note": "カイバーマン始動（r4）はサーチが最小で、灰への引きが浅い。"},
            ],
        },
        {
            "id": "d_veiler",
            "title": 'Effect Veiler',
            "jp": ext_jp['Effect Veiler'],
            "image_path": ext_img['Effect Veiler'],
            "effect": "相手フィールドのモンスター効果を無効にする（ターン限定）。",
            "events": ["field_eff"],
            "handlers": [
                {"label": "無効化された効果は飛ばして続行", "path": "continue", "note": "乙女・賢士・白石などのフィールド効果が殴られる。落ち着いて別のアクションに切り替える。"},
                {"label": "あまりフィールド効果を使わないルートへ", "path": {"route": "r3", "from_step": 0}, "note": "旋律始動（r3）は手札・魔法主体で、モンスター効果への引きが浅い。"},
            ],
        },
        {
            "id": "d_imperm",
            "title": 'Infinite Impermanence',
            "jp": ext_jp['Infinite Impermanence'],
            "image_path": ext_img['Infinite Impermanence'],
            "effect": "装着ターン中に相手フィールドのモンスター効果を無効化する魔法。",
            "events": ["field_eff", "spell"],
            "handlers": [
                {"label": "無効化された効果を飛ばして続行", "path": "continue", "note": "展開の途中でも1アクションの失敗は想定できる。落ち着いて打点盤面を固める。"},
                {"label": "フィールド効果に頼らないルートへ", "path": {"route": "r3", "from_step": 0}, "note": "旋律始動（r3）は魔法・墓地メインで、泡影の無効対象になりにくい。"},
            ],
        },
        {
            "id": "d_droll",
            "title": 'Droll & Lock Bird',
            "jp": ext_jp['Droll & Lock Bird'],
            "image_path": ext_img['Droll & Lock Bird'],
            "effect": "相手がサーチしたターン、自分はカードドローとサーチができない。",
            "events": ["search"],
            "handlers": [
                {"label": "サーチ先に代替を持っておく", "path": "continue", "note": "このターンのサーチはあきらめ、墓地・手札にある既存パーツで動く。"},
                {"label": "サーチに頼らないカイバーマンルートへ", "path": {"route": "r4", "from_step": 0}, "note": "カイバーマン始動（r4）はサーチが最小で、ドロールの効果を受けにくい。"},
            ],
        },
        {
            "id": "d_cbtg",
            "title": 'Called by the Grave',
            "jp": ext_jp['Called by the Grave'],
            "image_path": ext_img['Called by the Grave'],
            "effect": "墓地のモンスター効果（手札誘発含む）を無効化＋除外する。",
            "events": ["gy_eff"],
            "handlers": [
                {"label": "被らせない（白石graveを温存）", "path": "continue", "note": "墓地効果をいったん諦め、展開を切り上げて打点で押す。"},
                {"label": "墓地効果を使わないルートへ", "path": {"route": "r4", "from_step": 0}, "note": "カイバーマン始動（r4）は墓地効果に依存しない動きが多い。"},
            ],
        },
    ]

    tips = [
        "Blue-EyesはSS多めのテーマ。増殖するGを読んだら、SS数を減らせるルート（r3＝旋律始動）へ切り替えるのが基本。",
        "灰・ドロールはサーチの直前に打たれる。乙女（r1）・祭司（r2）を始動にする場合は、サーチを1回で済むカイバーマン（r4）に切り替えやすい。",
        "究極融合は速攻魔法なので、対戦中手札に1枚温存しておくと、盤面作戦の後盾として活かせる。",
    ]

    deck = {
        "theme": "blue-eyes",
        "draft": True,
        "meta": {
            "note": "本内容はドラフト版です。カード効果の正確な手順・順序は、実際の効果テキストと照らし合わせて修正してください。",
        },
        "deck": {
            "main": [entry_info(e) for e in main_entries],
            "extra": [entry_info(e) for e in extra_entries],
            "side": [],
        },
        "routes": routes,
        "disruptions": disruptions,
        "tips": tips,
    }

    #検証: image_path のファイルが存在すること & 参照カードの整合
    problems = []
    for sub in ("main", "extra", "side"):
        for e in deck["deck"][sub]:
            p = e.get("image_path")
            if not p or not (ROOT / p).exists():
                problems.append(f"{sub}: image missing for {e['name']}")
    for r in deck["routes"]:
        for i, s in enumerate(r["steps"]):
            c = s.get("card")
            if c:
                p = c.get("image_path")
                if not p or not (ROOT / p).exists():
                    problems.append(f"{r['id']} step{i + 1}: image missing for {c.get('name')}")
    for d in deck["disruptions"]:
        p = d.get("image_path")
        if not p or not (ROOT / p).exists():
            problems.append(f"disruption {d['id']}: image missing")
    if problems:
        print("VALIDATION_PROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1

    DECK_DIR.mkdir(parents=True, exist_ok=True)
    out = DECK_DIR / "blue-eyes.json"
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK wrote {out}")
    print(f"main={len(main_entries)} extra={len(extra_entries)} routes={len(routes)} disruptions={len(disruptions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
