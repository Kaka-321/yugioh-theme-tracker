# -*- coding: utf-8 -*-
"""Red Dragon Archfiend (レッド・デーモン) テンプレートデッキ + 展開ルート + 妨害対応データのビルドスクリプト。

- data/decks/red-dragon-archfiend.json を生成する (blue-eyes と同一スキーマ)。
- 共通外部カード (増G/灰流など) の画像は assets/cards/external/ を再利用する。
- 効果テキスト (ja_text) は desc_cache.json (Yugipedia) から供給する。
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_blue_eyes_deck import ensure_descs, load_desc_cache, slug, fetch_external_card, load_cache, save_cache
from fetch_blue_eyes_cards import ROOT

DECK_DIR = ROOT / "data" / "decks"

# RDA 用の外部カード (共通パック) — blue-eyes ですでに画像取得済み
EXTERNAL_TITLES = [
    'Maxx "C"',
    'Ash Blossom & Joyous Spring',
    'Effect Veiler',
    'Infinite Impermanence',
    'Called by the Grave',
    'Droll & Lock Bird',
]

DISRUPTION_TITLES = EXTERNAL_TITLES


def main():
    cache = load_cache()
    need = [t for t in EXTERNAL_TITLES if t not in cache]
    if need:
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
    theme_path = ROOT / "data" / "themes" / "red-dragon-archfiend.json"
    theme = json.loads(theme_path.read_text(encoding="utf-8"))
    by_id = {}
    for card in theme.get("cards", []):
        if isinstance(card, dict) and card.get("card_id") is not None:
            by_id[str(card["card_id"])] = card

    # ---- デッキ構成一覧 ----
    main_deck = [
        ("34761841", 3, "始動"),   # クリムゾン・リゾネーター
        ("62991792", 3, "始動"),   # ソウル・リゾネーター
        ("40975574", 2, "始動"),   # レッド・リゾネーター
        ("97021916", 2, "補助"),   # ダーク・リゾネーター
        ("14886469", 3, "展開"),   # レッド・スプリンター
        ("72318602", 2, "補助"),   # レッド・ガードナー
        ("45313993", 2, "展開"),   # レッド・ウルフ
        ("23008320", 3, "サーチ"), # コール・リゾネーター
        ("8559524", 1, "サーチ"),  # コマンド・リゾネーター
        ("98173209", 3, "展開"),   # クリムゾン・ヘルガイア
        ("99398682", 2, "展開"),   # クリムゾン・ヘルコール
        (None, 3, "妨害", 'Ash Blossom & Joyous Spring'),
        (None, 3, "妨害", 'Maxx "C"'),
        (None, 3, "妨害", 'Droll & Lock Bird'),
        (None, 3, "妨害", 'Infinite Impermanence'),
        (None, 2, "妨害", 'Called by the Grave'),
    ]
    extra_deck = [
        ("66141736", 2, "シンクロ"),  # レッド・ライジング・ドラゴン
        ("76547525", 1, "シンクロ"),  # レッド・ワイバーン
        ("70902743", 1, "レッド・デーモン"),  # レッド・デーモンズ・ドラゴン
        ("87451661", 1, "レッド・デーモン"),  # スカーレッド・デーモン
        ("39765958", 2, "レッド・デーモン"),  # 琰魔竜 レッド・デーモン
        ("80666118", 2, "レッド・デーモン"),  # レッド・デーモンズ・ドラゴン・スカーライト
        ("9753964", 1, "レッド・デーモン"),   # 琰魔竜 レッド・デーモン・アビス
        ("36857073", 1, "レッド・デーモン"),  # 琰魔竜 レッド・デーモン・ベリアル
        ("62242678", 1, "レッド・デーモン"),  # 琰魔竜王 レッド・デーモン・カラミティ
        ("16172067", 1, "レッド・デーモン"),  # レッド・デーモンズ・ドラゴン・タイラント
        ("97489701", 1, "レッド・デーモン"),  # スカーレッド・ノヴァ・ドラゴン
        ("99585850", 1, "レッド・デーモン"),  # スカーレッド・スーパーノヴァ・ドラゴン
    ]

    # ---- 効果テキスト (ja_text) & スペック取得 ----
    desc_cache = load_desc_cache()
    desc_titles = []
    for item in main_deck + extra_deck:
        if len(item) == 4 and item[0] is None:
            desc_titles.append(item[3])
        else:
            c = by_id.get(str(item[0]))
            if c:
                desc_titles.append(c["name"])
    desc_titles = sorted(set(t for t in desc_titles if t))
    desc_cache = ensure_descs(desc_titles, desc_cache)
    desc_by_name = {t: desc_cache.get(t, {}) for t in desc_titles}

    def _desc_fields(en_title):
        info = desc_by_name.get(en_title) or {}
        out = {}
        if info.get("ja_text"):
            out["desc"] = info["ja_text"]
        for k in ("types", "attribute", "level", "atk", "def"):
            if info.get(k):
                out[k] = info[k]
        return out

    def th(cid):
        card = by_id.get(str(cid))
        if card is None:
            raise KeyError(f"theme card missing: {cid}")
        return dict(
            {
                "en_name": card["name"],
                "card_id": card["card_id"],
                "name": card["japanese_name"] or card["name"],
                "image_path": card["image_path"],
                "external": False,
            },
            **_desc_fields(card["name"]),
        )

    def ex(title):
        return dict(
            {
                "en_name": title,
                "slug": ext[title]["slug"],
                "name": ext_jp[title],
                "image_path": ext_img[title],
                "external": True,
            },
            **_desc_fields(en_title=title),
        )

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
        info = {
            "card_id": e.get("card_id"),
            "slug": e.get("slug"),
            "name": e["name"],
            "image_path": e["image_path"],
            "external": bool(e["external"]),
            "count": e["count"],
            "role": e["role"],
        }
        info.update(_desc_fields(e.get("en_name") or ""))
        return info

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
            "name": "クリムゾン・リゾネーター始動（基本シンクロ）",
            "summary": "クリムゾン・リゾネーター1枚からスプリンターを絡めてライジング→琰魔竜のエース盤面。",
            "steps": [
                {"card": card("34761841"), "act": "特殊召喚", "note": "クリムゾン・リゾネーターを効果で特殊召喚（フィールドが空であれば可能）。",
                 "events": ["ss"],
                 "board": board(monsters=[card("34761841")], hand=[card("14886469"), card("34761841", "2枚目")])},
                {"card": card("14886469"), "act": "召喚", "note": "レッド・スプリンターを通常召喚。",
                 "events": [],
                 "board": board(monsters=[card("34761841"), card("14886469")], hand=[card("34761841", "2枚目")])},
                {"card": card("66141736"), "act": "シンクロ", "note": "クリムゾン（Lv2）＋スプリンター（Lv4）で、レッド・ライジング・ドラゴンをシンクロ召喚。",
                 "events": ["synchro"],
                 "board": board(monsters=[card("66141736")], gy=[card("34761841"), card("14886469")], extra=[card("66141736")])},
                {"card": card("34761841", "墓地から再展開"), "act": "効果", "note": "ライジングの効果で墓地のクリムゾン・リゾネーターを蘇生。",
                 "events": ["field_eff", "ss"],
                 "board": board(monsters=[card("34761841", "墓地から再展開"), card("66141736")], gy=[card("14886469")], extra=[card("66141736")])},
                {"card": card("39765958"), "act": "シンクロ", "note": "クリムゾン（Lv2）＋ライジング（Lv6）で、琰魔竜 レッド・デーモンをシンクロ召喚。全体除去からエースが立つ。",
                 "events": ["synchro"],
                 "board": board(monsters=[card("39765958")], gy=[card("14886469"), card("66141736"), card("34761841")], extra=[card("66141736")])},
                {"act": "盤面確定", "note": "終盤：琰魔竜 レッド・デーモン＋手札資源。打点とターン内強襲力の高い盤面。",
                 "board": board(monsters=[card("39765958")], gy=[card("14886469"), card("66141736"), card("34761841")], extra=[card("66141736")])},
            ],
        },
        {
            "id": "r2",
            "name": "琰魔竜王・カラミティ（12ロックルート）",
            "summary": "ライジングまでの同じ流れから、クリムゾンの2効果でリゾネーター2枚を特展開し、琰魔竜王 レッド・デーモン・カラミティを12で立てて相手をロックする。",
            "steps": [
                {"card": card("34761841"), "act": "特殊召喚", "note": "クリムゾン・リゾネーターを効果で特殊召喚。",
                 "events": ["ss"],
                 "board": board(monsters=[card("34761841")], hand=[card("72318602")])},
                {"card": card("72318602"), "act": "召喚", "note": "レッド・ガードナーを通常召喚。",
                 "events": [],
                 "board": board(monsters=[card("34761841"), card("72318602")], hand=[])},
                {"card": card("66141736"), "act": "シンクロ", "note": "クリムゾン（Lv2）＋ガードナー（Lv4）で、レッド・ライジング・ドラゴンをシンクロ。", "events": ["synchro"],
                 "board": board(monsters=[card("66141736")], gy=[card("34761841"), card("72318602")], extra=[card("66141736")])},
                {"card": card("34761841", "墓地から蘇生"), "act": "効果", "note": "ライジングの効果でクリムゾンを蘇生し、さらにクリムゾンの2効果でデッキからソウル・リゾネーターとダーク・リゾネーターを特殊召喚。",
                 "events": ["field_eff", "ss"],
                 "board": board(monsters=[card("34761841", "墓地から蘇生"), card("66141736"), card("62991792"), card("97021916")], gy=[card("72318602")], extra=[card("66141736")])},
                {"card": card("62242678"), "act": "シンクロ", "note": "ソウル（Lv3）＋ダーク（Lv3）＋ライジング（Lv6）＝12で、琰魔竜王 レッド・デーモン・カラミティをシンクロ召喚。発動効果で相手のカード発動を1ターン無効化。",
                 "events": ["synchro"],
                 "board": board(monsters=[card("34761841", "墓地から蘇生"), card("62242678")], gy=[card("72318602"), card("66141736"), card("62991792"), card("97021916")], extra=[card("66141736")])},
                {"act": "盤面確定", "note": "終盤：琰魔竜 カラミティ＋クリムゾン。12ロックで相手ターンを封じて殴る盤面。",
                 "board": board(monsters=[card("34761841", "墓地から蘇生"), card("62242678")], gy=[card("72318602"), card("66141736"), card("62991792"), card("97021916")], extra=[card("66141736")])},
            ],
        },
        {
            "id": "r3",
            "name": "琰魔竜 レッド・デーモン・アビス（無効＋蘇生）",
            "summary": "クリムゾンの2効果でソウル・リゾネーターを場に足し、ライジングと Together 12ではなく9でアビスを立てる妨害重視ルート。",
            "steps": [
                {"card": card("34761841"), "act": "特殊召喚", "note": "クリムゾン・リゾネーターを効果で特殊召喚。",
                 "events": ["ss"],
                 "board": board(monsters=[card("34761841")], hand=[card("14886469")])},
                {"card": card("14886469"), "act": "召喚", "note": "レッド・スプリンターを通常召喚。",
                 "events": [],
                 "board": board(monsters=[card("34761841"), card("14886469")], hand=[])},
                {"card": card("66141736"), "act": "シンクロ", "note": "クリムゾン（Lv2）＋スプリンター（Lv4）で、レッド・ライジング・ドラゴンをシンクロ。",
                 "events": ["synchro"],
                 "board": board(monsters=[card("66141736")], gy=[card("34761841"), card("14886469")], extra=[card("66141736")])},
                {"card": card("34761841", "墓地から蘇生"), "act": "効果", "note": "ライジングの効果でクリムゾンを蘇生し、クリムゾンの2効果でデッキからソウル・リゾネーターを特殊召喚。",
                 "events": ["field_eff", "ss"],
                 "board": board(monsters=[card("34761841", "墓地から蘇生"), card("66141736"), card("62991792")], gy=[card("14886469")], extra=[card("66141736")])},
                {"card": card("9753964"), "act": "シンクロ", "note": "ソウル（Lv3）＋ライジング（Lv6）＝9で、琰魔竜 レッド・デーモン・アビスをシンクロ召喚。相手のカード効果を無効化できる強力な妨害層。",
                 "events": ["synchro"],
                 "board": board(monsters=[card("34761841", "墓地から蘇生"), card("9753964")], gy=[card("14886469"), card("66141736"), card("62991792")], extra=[card("66141736")])},
                {"act": "盤面確定", "note": "終盤：アビス＋クリムゾン。クイック効果の無効化と戦闘ダメージ後の蘇生で持続的に抑える。",
                 "board": board(monsters=[card("34761841", "墓地から蘇生"), card("9753964")], gy=[card("14886469"), card("66141736"), card("62991792")], extra=[card("66141736")])},
            ],
        },
        {
            "id": "r4",
            "name": "レッド・デーモンズ・ドラゴン本体（ワイバーン経由）",
            "summary": "ソウル・リゾネーターとレッド・ウルフで場を整え、クリムゾンを Adding してレッド・デーモンのシンクロや本体（レッド・デーモンズ・ドラゴン）まで進めるルート。",
            "steps": [
                {"card": card("62991792"), "act": "召喚", "note": "ソウル・リゾネーターを通常召喚。効果でデッキからレベル4以下の悪魔族（レッド・スプリンターなど）を手札へ。",
                 "events": ["field_eff", "search"],
                 "board": board(monsters=[card("62991792")], hand=[card("14886469")])},
                {"card": card("45313993"), "act": "特殊召喚", "note": "ソウル（リゾネーター）の召喚をトリガーに、レッド・ウルフを手札から特殊召喚（攻撃力半減）。",
                 "events": ["ss"],
                 "board": board(monsters=[card("62991792"), card("45313993", "攻撃力半減")], hand=[card("14886469")])},
                {"card": card("34761841"), "act": "特殊召喚", "note": "クリムゾン・リゾネーターを効果で特殊召喚。",
                 "events": ["ss"],
                 "board": board(monsters=[card("62991792"), card("45313993", "攻撃力半減"), card("34761841")], hand=[card("14886469")])},
                {"card": card("87451661"), "act": "シンクロ", "note": "クリムゾン（Lv2）＋レッド・ウルフ（Lv6）＝8で、スカーレッド・デーモンをシンクロ召喚（効果でカード名が「レッド・デーモン」として扱われる）。",
                 "events": ["synchro"],
                 "board": board(monsters=[card("62991792"), card("87451661")], gy=[card("34761841"), card("45313993")], extra=[card("87451661")])},
                {"card": card("70902743"), "act": "シンクロ", "note": "レッド・リゾネーター（Lv2）＋墓地のワイバーン展開??実際には、ソウル・リゾネーター（Lv3）＋スカーレッド・デーモン（Lv8）＝11。ここではスカーレッド・デーモンをそのまま残し、追加シンクロの実現（無料）ではなく手札のスパイター等で次ターンへ繋ぐ準備。",
                 "events": ["note"],
                 "board": board(monsters=[card("62991792"), card("87451661")], gy=[card("34761841"), card("45313993")], extra=[card("87451661")])},
                {"act": "盤面確定", "note": "終盤：スカーレッド・デーモン＋ソウル。スカーレッド・デーモンの効果は墓地へ送られた時、レッド・デーモン（本体）をシンクロ扱いで展開可能。",
                 "board": board(monsters=[card("62991792"), card("87451661")], gy=[card("34761841"), card("45313993")], extra=[card("87451661")])},
            ],
        },
        {
            "id": "r5",
            "name": "スカーライト・バーン（ダブル除去）",
            "summary": "ガードナー始動の逆バージョン。ライジングを立ててからスカーライトをシンクロし、S特殊召喚モンスターを一掃するバーン系の強襲ルート。",
            "steps": [
                {"card": card("34761841"), "act": "特殊召喚", "note": "クリムゾン・リゾネーターを効果で特殊召喚。",
                 "events": ["ss"],
                 "board": board(monsters=[card("34761841")], hand=[card("72318602")])},
                {"card": card("72318602"), "act": "召喚", "note": "レッド・ガードナーを通常召喚。",
                 "events": [],
                 "board": board(monsters=[card("34761841"), card("72318602")], hand=[])},
                {"card": card("66141736"), "act": "シンクロ", "note": "クリムゾン（Lv2）＋ガードナー（Lv4）で、レッド・ライジング・ドラゴンをシンクロ。",
                 "events": ["synchro"],
                 "board": board(monsters=[card("66141736")], gy=[card("34761841"), card("72318602")], extra=[card("66141736")])},
                {"card": card("34761841", "墓地から蘇生"), "act": "効果", "note": "ライジングの効果でクリムゾンを蘇生。",
                 "events": ["field_eff", "ss"],
                 "board": board(monsters=[card("34761841", "墓地から蘇生"), card("66141736")], gy=[card("72318602")], extra=[card("66141736")])},
                {"card": card("80666118"), "act": "シンクロ", "note": "クリムゾン（Lv2）＋ライジング（Lv6）＝8で、レッド・デーモンズ・ドラゴン・スカーライトをシンクロ召喚。効果で特殊召喚されたモンスターを一掃し、破壊数×500ダメージ。",
                 "events": ["synchro"],
                 "board": board(monsters=[card("80666118")], gy=[card("72318602"), card("66141736"), card("34761841")], extra=[card("66141736")])},
                {"act": "盤面確定", "note": "終盤：スカーライト。除去バーンで展開デッキに強く、打点3000で攻めていける。",
                 "board": board(monsters=[card("80666118")], gy=[card("72318602"), card("66141736"), card("34761841")], extra=[card("66141736")])},
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
                {"label": "このまま押し切る", "path": "continue", "note": "打点prioritizeで一気に押し切る（後手からの大打撃を狙う）。"},
                {"label": "SS数を絞ったルートへ", "path": {"route": "r4", "from_step": 0}, "note": "r4（ソウル+ウルフ開始）は展開SSが少なく、Gへのドロー供給を抑えやすい。"},
            ],
        },
        {
            "id": "d_ash",
            "title": "Ash Blossom & Joyous Spring",
            "jp": ext_jp["Ash Blossom & Joyous Spring"],
            "image_path": ext_img["Ash Blossom & Joyous Spring"],
            "effect": "サーチ・墓地送り・EXからの特殊召喚を無効にする。",
            "events": ["search", "ss", "gy_eff"],
            "handlers": [
                {"label": "切断されたアクションを飛ばして続行", "path": "continue", "note": "クリムゾン展開やコール・リゾネーターのサーチ妨害を飛ばし、現存資源で盤面を作る。"},
                {"label": "展開し続ける（クリムゾン再利用）", "path": {"route": "r1", "from_step": 0}, "note": "クリムゾンの手札・デッキ特殊召喚を軸にしたr1は継続しやすい。"},
            ],
        },
        {
            "id": "d_veiler",
            "title": "Effect Veiler",
            "jp": ext_jp["Effect Veiler"],
            "image_path": ext_img["Effect Veiler"],
            "effect": "相手フィールドのモンスター効果を無効にする（ターン限定）。",
            "events": ["field_eff"],
            "handlers": [
                {"label": "無効化された効果は飛ばして続行", "path": "continue", "note": "クリムゾン蘇生やライジングの効果を飛ばし、シンクロ主体で進める。"},
                {"label": "フィールド効果を絞ったルートへ", "path": {"route": "r1", "from_step": 0}, "note": "r1はシンクロと召喚中心で、モンスター効果の依存を抑えられる。"},
            ],
        },
        {
            "id": "d_imperm",
            "title": "Infinite Impermanence",
            "jp": ext_jp["Infinite Impermanence"],
            "image_path": ext_img["Infinite Impermanence"],
            "effect": "装着ターン中に相手フィールドのモンスター効果を無効化する魔法。",
            "events": ["field_eff", "spell"],
            "handlers": [
                {"label": "無効化された効果を飛ばして続行", "path": "continue", "note": "1アクションの無効はクリムゾンの追加展開で回収できる。"},
                {"label": "展開し続ける（クリムゾン利用）", "path": {"route": "r1", "from_step": 0}, "note": "クリムゾン始動はそのまま影響を受けにくく回復が効く。"},
            ],
        },
        {
            "id": "d_droll",
            "title": "Droll & Lock Bird",
            "jp": ext_jp["Droll & Lock Bird"],
            "image_path": ext_img["Droll & Lock Bird"],
            "effect": "相手がサーチしたターン、自分はカードドローとサーチができない。",
            "events": ["search"],
            "handlers": [
                {"label": "サーチ先に代替を持っておく", "path": "continue", "note": "コール・リゾネーターで引かれても手札・墓地にある層で継続。"},
                {"label": "サーチに依存しない動きへ", "path": {"route": "r1", "from_step": 0}, "note": "クリムゾン始動はデッキ特殊召喚主体でドロックの効果は最小限。"},
            ],
        },
        {
            "id": "d_cbtg",
            "title": "Called by the Grave",
            "jp": ext_jp["Called by the Grave"],
            "image_path": ext_img["Called by the Grave"],
            "effect": "墓地のモンスター効果（手札誘発含む）を無効化＋除外する。",
            "events": ["gy_eff"],
            "handlers": [
                {"label": "被らせない（蘇生先を温存）", "path": "continue", "note": "ライジングの蘇生先が断たれても、残りのリゾネーターでシンクロし直す。"},
                {"label": "墓地効果に頼らないルートへ", "path": {"route": "r4", "from_step": 0}, "note": "r4は墓地効果を経由しないシンクロ展開が主軸。"},
            ],
        },
    ]

    tips = [
        "レッド・デーモンはシンクロ多用テーマ。クリムゾン・リゾネーターを起点に、ライジング→12ロック（カラミティ）か9妨害（アビス）で駒を残すのが基本。",
        "レッド・ウルフはリゾネーターの召喚に合わせて手札から出せるので、ソウル・リゾネーターとセットで使うとワンカードから8体まで届く。",
        "スカーレッド・デーモン・タイラントやノヴァ・ドラゴンは、墓地リーを戦闘で回しつつ最終盤面として狙える（ドラフトでは未追求）。",
    ]

    deck = {
        "theme": "red-dragon-archfiend",
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

    total_main = sum(e["count"] for e in deck["deck"]["main"])
    total_extra = sum(e["count"] for e in deck["deck"]["extra"])
    if total_main != 40 or total_extra != 15:
        print(f"CARD_COUNT_MISMATCH main={total_main} extra={total_extra}")
        return 1

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
                    problems.append(f"{r['id']} step{i+1}: image missing for {c.get('name')}")
            for zone in ("monsters", "spells", "hand", "gy", "banish", "extra"):
                for c in (s.get("board") or {}).get(zone) or []:
                    if c:
                        p = c.get("image_path")
                        if not p or not (ROOT / p).exists():
                            problems.append(f"{r['id']} step{i+1} {zone}: image missing for {c.get('name')}")
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
    out = DECK_DIR / "red-dragon-archfiend.json"
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK wrote {out}")
    print(f"main={len(main_entries)} extra={len(extra_entries)} routes={len(routes)} disruptions={len(disruptions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
