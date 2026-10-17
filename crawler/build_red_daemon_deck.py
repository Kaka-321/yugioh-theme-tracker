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
    'Foolish Burial',
    'Skull Meister',
    'Ghost Belle & Haunted Mansion',
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

    # ---- デッキ構成一覧（2026環境のチェーン・デーモン / Konami DB トーナメント準拠） ----
    main_deck = [
        ("19434243", 3, "始動"),    # パワー・バイス・ドラゴン
        ("56838842", 1, "補助"),    # デモン・ピース・ゴーレム
        ("25784595", 3, "展開"),    # ボーン・デーモン
        ("62991792", 2, "始動"),    # ソウル・リゾネーター
        ("83445539", 1, "展開"),    # ダークネス・リゾネーター
        ("34761841", 1, "始動"),    # クリムゾン・リゾネーター
        ("98396890", 1, "展開"),    # ヴィジョン・リゾネーター
        ("77360173", 1, "展開"),    # シンクローン・リゾネーター
        ("13764881", 1, "展開"),    # チェーン・リゾネーター
        ("32731036", 1, "展開"),    # 深淺の獣ルベリオン
        ("33854624", 1, "展開"),    # 深淺の獣マグナムート
        ("70088809", 1, "展開"),    # 調和ノ天救竜
        (None, 1, "妨害", "Skull Meister"),
        (None, 3, "妨害", "Ash Blossom & Joyous Spring"),
        (None, 1, "妨害", "Ghost Belle & Haunted Mansion"),
        (None, 1, "妨害", 'Maxx "C"'),
        (None, 2, "妨害", "Droll & Lock Bird"),
        ("98173209", 3, "サーチ"),  # クリムゾン・ヘルガイア
        ("23008320", 2, "サーチ"),  # コール・リゾネーター
        (None, 1, "展開", "Foolish Burial"),
        ("99398682", 1, "サーチ"),  # クリムゾン・ヘルコール
        ("40366667", 2, "妨害"),    # 霊王の波動
        (None, 3, "妨害", "Infinite Impermanence"),
        ("17269895", 1, "妨害"),    # 覇者の鳴動
        ("50056656", 1, "妨害"),    # スカーレッド・ゾーン
        ("92936364", 1, "妨害"),    # レッド・デーモンズ・チェーン
    ]
    extra_deck = [
        ("30698243", 1, "レッド・デーモン"),   # レッド・デーモンズ・ドラゴン・ハイパーノヴァ → Red Hypernova Dragon
        ("99585850", 1, "レッド・デーモン"),   # スカーレッド・スーパーノヴァ・ドラゴン
        ("65541655", 1, "レッド・デーモン"),   # スカーレッド・ノヴァ・ドラゴン－バーニング・ソウル
        ("29053656", 1, "シンクロ"),           # 赤き竜 ケッツァーコアトル
        ("94641726", 1, "シンクロ"),           # 嵐忌竜デストゥビム
        ("27572350", 1, "シンクロ"),           # 深淺の神獣ディス・パテル
        ("9753964", 1, "レッド・デーモン"),    # 琰魔竜 レッド・デーモン・アビス
        ("67809530", 1, "シンクロ"),           # 紅蓮の王者
        ("87451661", 1, "レッド・デーモン"),   # スカーレッド・デーモン
        ("70902743", 2, "レッド・デーモン"),   # レッド・デーモンズ・ドラゴン
        ("4891376", 1, "シンクロ"),            # 鎖縛竜ザレン
        ("3294539", 1, "シンクロ"),            # クリムゾン・ブレード・ドラゴン
        ("66141736", 2, "シンクロ"),           # レッド・ライジング・ドラゴン
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
            "name": "パワー・バイス・ドラゴン始動（ハイパーノヴァ/赤き竜）",
            "summary": "パワー・バイス・ドラゴンの自己特殊召喚からダークネス・リゾネーターを絡め、ボーン・デーモン展開でスカーレッド・ハイパーノヴァ＋赤き竜 ケッツァーコアトルまで突き上げる最長ルート。",
            "steps": [
                {
                    "label": "①パワー・バイス・ドラゴン 特殊召喚",
                    "card": card("19434243", "手札から特殊召喚（①）"),
                    "board": board(monsters=[card("19434243")], hand=[card("83445539")]),
                    "note": "自分・相手のモンスターが存在しない場合に自己特殊召喚（①）。成功後、デッキからダークネス・リゾネーターを手札に加える（②）。",
                },
                {
                    "label": "②ダークネス・リゾネーター 特殊召喚",
                    "card": card("83445539", "EXのレッド・デーモンズ・ドラゴンを披露"),
                    "board": board(monsters=[card("19434243"), card("83445539")]),
                    "note": "EXデッキのレッド・デーモンズ・ドラゴンを相手に見せて手札から特殊召喚。追加で通常召喚権を得る（②）。",
                },
                {
                    "label": "③紅蓮の王者 シンクロ（5+1）",
                    "card": card("67809530"),
                    "board": board(monsters=[card("67809530")], gy=[card("19434243"), card("83445539")], extra=[th("70902743")]),
                    "note": "パワー・バイス(5)+ダークネス(1)で紅蓮の王者(6)。墓地のリゾネーターはヘルコールのサーチ先として再利用可能。",
                },
                {
                    "label": "④ヘルコール → チェーン・リゾネーター",
                    "card": card("99398682"),
                    "board": board(monsters=[card("67809530")], gy=[th("99398682")], hand=[card("13764881"), card("98173209")]),
                    "note": "ヘルコールを発動しデッキからチェーン・リゾネーターを手札へ。紅蓮の王者①でヘルガイアを手札に加えておく。",
                },
                {
                    "label": "⑤チェーン召喚 → ソウル特召 → ボーン・サーチ",
                    "card": card("13764881"),
                    "board": board(monsters=[card("67809530"), card("13764881"), card("62991792")], hand=[card("25784595")], gy=[th("99398682")]),
                    "note": "チェーン・リゾネーター(1)を召喚し、②でソウル・リゾネーターを手札から特殊召喚。ソウル①でボーン・デーモンをサーチ。",
                },
                {
                    "label": "⑥ボーン効果 → ライジング S → クリムゾン蘇生",
                    "card": card("25784595"),
                    "board": board(monsters=[card("67809530"), card("66141736")], hand=[card("34761841")], gy=[card("19434243"), card("83445539"), card("62991792"), th("99398682")], extra=[th("70902743")]),
                    "note": "ボーンの効果で手札のクリムゾンを墓地へ送り自分のレベルを3に調整。ソウル(3)+ボーン(3)でライジング(6)。ライジング①でクリムゾンを蘇生。",
                },
                {
                    "label": "⑦クリムゾン② → シンクローン+ダークネス 特殊召喚",
                    "card": card("34761841"),
                    "board": board(monsters=[card("67809530"), card("66141736"), card("77360173"), card("83445539")], gy=[card("19434243"), card("62991792"), th("99398682")], extra=[th("70902743")]),
                    "note": "クリムゾン②でシンクローン・リゾネーターとダークネス・リゾネーターをデッキから特殊召喚。",
                },
                {
                    "label": "⑧クリムゾン・ブレード S（6+1）→ ルベリオン・サーチ",
                    "card": card("3294539"),
                    "board": board(monsters=[card("67809530"), card("3294539"), card("83445539")], hand=[card("32731036")], gy=[card("19434243"), card("62991792"), th("99398682")], extra=[th("70902743")]),
                    "note": "ライジング(6)+シンクローン(1)でクリムゾン・ブレード・ドラゴン(7)。効果で深淺の獣ルベリオンを手札に加える。",
                },
                {
                    "label": "⑨スカーレッド・ハイパーノヴァ S（合計12）",
                    "card": th("30698243"),
                    "board": board(monsters=[card("67809530"), th("30698243")], gy=[card("19434243"), card("62991792"), th("99398682"), card("34761841")], extra=[th("70902743")]),
                    "note": "ブレード(7)+ダークネス(1)+シンクローン(1)+チェーン(1)+クリムゾン(蘇生2)でスカーレッド・ハイパーノヴァ(12+)。",
                },
                {
                    "label": "⑩ディスパテル→赤き竜→盤面完成",
                    "card": th("29053656"),
                    "board": board(monsters=[th("30698243"), th("29053656"), card("67809530")], spells=[card("50056656", "スカーレッド・ゾーン セット")], gy=[card("19434243"), card("62991792"), th("99398682"), card("34761841")], extra=[th("70902743")]),
                    "note": "ルベリオンとヴィジョンで深淺の神獣ディス・パテル、ディスパテルとヴィジョンで赤き竜 ケッツァーコアトル。スカーレッド・ゾーンを伏せて完成（Konami DB トーナメント最終盤面を簡略化）。",
                },
            ],
        },
        {
            "id": "r2",
            "name": "ソウル・リゾネーター始動（スーパーノヴァ盤面）",
            "summary": "ソウル・リゾネーター×ボーン・デーモンでライジングを展開し、クリムゾンの蘇生効果からシンクローンを絡めてスカーレッド・スーパーノヴァ・ドラゴンまで持っていく基本2ルート。",
            "steps": [
                {
                    "label": "①ソウル召喚 → ボーン・サーチ",
                    "card": card("62991792"),
                    "board": board(monsters=[card("62991792")], hand=[card("25784595")]),
                    "note": "ソウル・リゾネーターを召喚し、①でデッキからレベル4以下の「デーモン」モンスター＝ボーン・デーモンを手札へ。",
                },
                {
                    "label": "②ボーン 特殊召喚（クリムゾン墓地送り）",
                    "card": card("25784595"),
                    "board": board(monsters=[card("62991792"), card("25784595")], gy=[th("98173209")]),
                    "note": "手札1枚（例: ガイア）をコストに墓地へ送り自分のレベルを3に。ソウル(3)+ボーン(3)の素材が揃う。",
                },
                {
                    "label": "③ライジング S → クリムゾン蘇生",
                    "card": card("66141736"),
                    "board": board(monsters=[card("66141736"), card("34761841")], gy=[card("62991792"), th("98173209")], extra=[th("70902743")]),
                    "note": "ソウル+ボーンでレッド・ライジング・ドラゴン(6)。ライジング①で墓地のクリムゾン・リゾネーターを蘇生。",
                },
                {
                    "label": "④クリムゾン② → シンクローン+ダークネス 特殊召喚",
                    "card": card("34761841"),
                    "board": board(monsters=[card("66141736"), card("34761841"), card("77360173"), card("83445539")], gy=[card("62991792"), th("98173209")], extra=[th("70902743")]),
                    "note": "クリムゾン②でシンクローン・リゾネーターとダークネス・リゾネーターをデッキから特殊召喚。",
                },
                {
                    "label": "⑤スカーレッド・デーモン S（6+2）",
                    "card": card("87451661"),
                    "board": board(monsters=[th("87451661")], gy=[card("62991792"), th("98173209")], extra=[th("70902743")]),
                    "note": "ライジング(6)+ヴィジョン・リゾネーター(2)でスカーレッド・デーモン(8)。ヴィジョンはヘルコール/ヘルガイアのサーチで手札に確保しておく (ヘルコール or ヘルガイア)。",
                },
                {
                    "label": "⑥スーパーノヴァ S（合計12+）",
                    "card": th("99585850"),
                    "board": board(monsters=[th("99585850")], spells=[card("50056656", "スカーレッド・ゾーン セット")], gy=[card("62991792"), th("98173209")], extra=[th("70902743")]),
                    "note": "スカーレッド・デーモン(8)+クリムゾン(2)+シンクローン(1)+ダークネス(1)でスカーレッド・スーパーノヴァ・ドラゴン。",
                },
            ],
        },
        {
            "id": "r3",
            "name": "ガイア始動（琰魔竜アビス盤面）",
            "summary": "クリムゾン・ヘルガイアでクリムゾン・リゾネーターを展開し、琰魔竜 レッド・デーモン・アビスを中心にした妨害母体を作るルート。",
            "steps": [
                {
                    "label": "①ヘルガイア発動 → クリムゾン 特殊召喚",
                    "card": card("98173209"),
                    "board": board(monsters=[card("34761841")], gy=[th("98173209")]),
                    "note": "クリムゾン・ヘルガイアの①効果でデッキからクリムゾン・リゾネーターを特殊召喚（リゾネーター1体を墓地へ）。",
                },
                {
                    "label": "②クリムゾン② → シンクローン+ダークネス 特殊召喚",
                    "card": card("34761841"),
                    "board": board(monsters=[card("34761841"), card("77360173"), card("83445539")], gy=[th("98173209")]),
                    "note": "クリムゾン②でシンクローン・リゾネーターとダークネス・リゾネーターをデッキから特殊召喚。",
                },
                {
                    "label": "③レッド・デーモンズ・ドラゴン S",
                    "card": card("70902743"),
                    "board": board(monsters=[card("70902743")], gy=[card("34761841"), th("98173209")], extra=[th("70902743")]),
                    "note": "クリムゾン(2)+ダークネス(1)+シンクローン(1)+ボーン(レベル3化3)詳細は効果テキスト参照でレッド・デーモンズ・ドラゴン。",
                },
                {
                    "label": "④アビス S → スカーレッド・ゾーン セット",
                    "card": card("9753964"),
                    "board": board(monsters=[card("9753964")], spells=[card("50056656", "スカーレッド・ゾーン セット")], gy=[card("34761841"), th("98173209")], extra=[th("70902743")]),
                    "note": "ソウル・リゾネーター(3)+デーモンズ・ドラゴン(8+?)等で琰魔竜 レッド・デーモン・アビス。スカーレッド・ゾーンを伏せて妨害を準備。",
                },
            ],
        },
    ]

    # ---- 妨害カード ----
    disruptions = [
        dict(
            card("98396890") if False else dict(
                en_name="Ash Blossom & Joyous Spring", slug="ash-blossom-joyous-spring",
                name=ext_jp["Ash Blossom & Joyous Spring"], image_path=ext_img["Ash Blossom & Joyous Spring"], external=True,
                **_desc_fields("Ash Blossom & Joyous Spring")),
            id="d_ash", title="灰流うらら",
            effect="モンスター効果・魔法・罠の「墓地を含むデッキ・EXからのカード操作」を無効化できる万能手札誘発。",
            events=["search", "ss", "gy_eff"],
            handlers=[
                {"label": "サーチ打ち切り（展開短縮）", "path": "continue", "note": "ボーン/ルベリオン等のサーチが止まって盤面規模が縮む。"},
                {"label": "無効化を通されず継続", "path": "continue", "note": "相手に無効化を通されずルート続行。"},
            ],
        ),
        dict(
            dict(en_name='Maxx "C"', slug='maxx-c', name=ext_jp['Maxx "C"'], image_path=ext_img['Maxx "C"'], external=True, **_desc_fields('Maxx "C"')),
            id="d_g", title="増殖するG",
            effect="相手の特殊召喚のたびに自分のドロー数決定。展開テーマへ最も脅威なけん制。",
            events=["ss"],
            handlers=[
                {"label": "Gを踏まずに固く動く", "path": "continue", "note": "展開を最小限に留め、罠ゾーンで止める。"},
                {"label": "ノーと宣言し展開継続", "path": "continue", "note": "Gを引かれても手札と罠で勝負。"},
            ],
        ),
        dict(
            dict(en_name="Droll & Lock Bird", slug="droll-lock-bird", name=ext_jp["Droll & Lock Bird"], image_path=ext_img["Droll & Lock Bird"], external=True, **_desc_fields("Droll & Lock Bird")),
            id="d_droll", title="ドロール＆ロックバード",
            effect="相手ターンにサーチ操作が発生した際、そのターン中デッキからのサーチ禁止。",
            events=["search"],
            handlers=[
                {"label": "サーチ絡みのルートを切替", "path": {"route": "r3", "from_step": 0}, "note": "サーチなしでも動けるガイア始動へ。"},
                {"label": "継続", "path": "continue", "note": "以降の展開はボーン〜既存手札で回す。"},
            ],
        ),
        dict(
            dict(en_name="Ghost Belle & Haunted Mansion", slug="ghost-belle-haunted-mansion", name=ext_jp["Ghost Belle & Haunted Mansion"], image_path=ext_img["Ghost Belle & Haunted Mansion"], external=True, **_desc_fields("Ghost Belle & Haunted Mansion")),
            id="d_belle", title="墓荒らし",
            effect="墓地のモンスター効果・墓地からの除外・デッキからの墓地送りを無効化。",
            events=["gy_eff"],
            handlers=[
                {"label": "墓地送りのコストを止める", "path": "continue", "note": "ボーン素材のクリムゾン送り等が断たれルート分断へ。"},
                {"label": "継続", "path": "continue", "note": "別の展開先へ。"},
            ],
        ),
        dict(
            dict(en_name="Infinite Impermanence", slug="infinite-impermanence", name=ext_jp["Infinite Impermanence"], image_path=ext_img["Infinite Impermanence"], external=True, **_desc_fields("Infinite Impermanence")),
            id="d_imperm", title="無限泡影",
            effect="フィールドのモンスター効果無効化＋該当ゾーン封じ。対象カードが残ると展開が止まる。",
            events=["field_eff", "ss", "spell"],
            handlers=[
                {"label": "効果を封じられ継続", "path": "continue", "note": "展開の要が無効になれば盤面規模は縮む。"},
                {"label": "別ルートへ切替", "path": {"route": "r3", "from_step": 0}, "note": "罠主体の小さな盤面へ。"},
            ],
        ),
        dict(
            dict(card("40366667"), id="d_wave", title="霊王の波動",
                 effect="モンスター効果の無効化＋除外を絡めるモンスター効果を無効化し除外も絡めて妨害できる強力な罠（詳細は効果テキスト）。"),
            events=["field_eff", "ss"],
            handlers=[
                {"label": "効果を封じられ継続", "path": "continue", "note": "重要ポイントでのみ使用。"},
                {"label": "再展開へ", "path": {"route": "r2", "from_step": 0}, "note": "ソウルルートへ切替。"},
            ],
        ),
        dict(
            dict(card("17269895"), id="d_resonance", title="覇者の鳴動",
                 effect="EXからの特殊召喚を伴うシンクロ展開への止めとして機能する永続風の妨害（詳細は効果テキスト）。"),
            events=["synchro", "ss"],
            handlers=[
                {"label": "シンクロを止める", "path": "continue", "note": "EXの主要カードが墓庭や手札に積まれる。"},
                {"label": "継続", "path": "continue"},
            ],
        ),
    ]

    tips = [
        "2026環境の「チェーン・デーモン」。パワー・バイス・ドラゴン/ダークネス・リゾネーター/ボーン・デーモンが がルートの中核。",
        "クリムゾン②のシンクローン+ダークネス特殊召喚が一番のエンジン。守りに回ると盤面が縮む。拘束せず、ライジング→クリムゾン蘇生の2連シンクロで拡大。",
        "EXはハイパーノヴァ/スーパーノヴァ/赤き竜の三本柱。各種テーマトラップ（霊王の波動/覇者の鳴動/スカーレッド・ゾーン）が引き当たるり展開の妨害として活躍。",
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
