#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""routes を 1ステップ=1アクション の細粒度に分解し直す。ボードはアクション列からの一貫再構築。"""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK_PATH = os.path.join(ROOT, "data/decks/red-dragon-archfiend.json")


class Board:
    def __init__(self, hand):
        self.mons = []
        self.spells = []
        self.hand = list(hand)
        self.gy = []
        self.extra = []
        self.banish = []

    def snapshot(self):
        if len(self.mons) > 5 or len(self.spells) > 5:
            raise RuntimeError("zone overflow: mons=%d spells=%d" % (len(self.mons), len(self.spells)))
        return {
            "monsters": [copy.deepcopy(x) for x in self.mons] + [None] * (5 - len(self.mons)),
            "spells": [copy.deepcopy(x) for x in self.spells] + [None] * (5 - len(self.spells)),
            "hand": copy.deepcopy(self.hand),
            "gy": copy.deepcopy(self.gy),
            "banish": copy.deepcopy(self.banish),
            "extra": copy.deepcopy(self.extra),
        }

    def drop(self, name):
        self.hand = [e for e in self.hand if e["name"] != name]

    def keep(self, names):
        self.mons = [e for e in self.mons if e["name"] in names]


def main():
    deck = json.load(open(DECK_PATH, encoding="utf-8"))
    N0 = {}
    for bag in ("main", "extra"):
        for e in deck["deck"][bag]:
            N0.setdefault(e["name"], e)
    NS = {}

    def N(n):
        return copy.deepcopy(N0[n])

    def route(hand, acts):
        B = Board([N0[x] for x in hand])
        steps = []
        no = 0
        for a in acts:
            no += 1
            a["fn"](B)
            steps.append({
                "label": "%d. %s" % (no, a["text"]),
                "act": a.get("act") or "アクション",
                "card": copy.deepcopy(N0[a["card"]]) if a.get("card") else None,
                "note": a["note"],
                "board": B.snapshot(),
            })
        return steps

    # ===== r1 パワー・バイス始動（ハイパーノヴァ/赤き竜） =====
    r1 = route(["クリムゾン・リゾネーター"], [
        dict(text="パワー・バイス・ドラゴン 特殊召喚", act="特殊召喚", card="パワー・バイス・ドラゴン",
             note="自分・相手のモンスターが存在しない場合に自己特殊召喚（①）。",
             fn=lambda b: b.mons.append(N("パワー・バイス・ドラゴン"))),
        dict(text="パワー・バイス②：ダークネス・リゾネーターをサーチ", act="効果", card="パワー・バイス・ドラゴン",
             note="デッキから「リゾネーター」＝ダークネス・リゾネーターを手札に加える。",
             fn=lambda b: b.hand.append(N("ダークネス・リゾネーター"))),
        dict(text="ダークネス・リゾネーター 特殊召喚", act="特殊召喚", card="ダークネス・リゾネーター",
             note="EXデッキの「レッド・デーモンズ・ドラゴン」を相手に見せて自己特殊召喚（①）。このターンはＳモンスターしかEXから特殊召喚できない。通常召喚権を1つ追加で得る（②）。",
             fn=lambda b: (b.mons.append(N("ダークネス・リゾネーター")), b.extra.append(N("レッド・デーモンズ・ドラゴン")),
                           b.drop("ダークネス・リゾネーター"))),
        dict(text="紅蓮の王者 シンクロ（5+3）", act="シンクロ", card="紅蓮の王者",
             note="パワー・バイス(5)+ダークネス(3)で紅蓮の王者(8)。素材2体は墓地へ。",
             fn=lambda b: (b.gy.extend([N("パワー・バイス・ドラゴン"), N("ダークネス・リゾネーター")]),
                           b.mons.clear(), b.mons.append(N("紅蓮の王者")))),
        dict(text="紅蓮の王者①：レッド・デーモンズ・ドラゴンの名を記したカード＝ヘルコールをサーチ", act="効果", card="紅蓮の王者",
             note="デッキから「クリムゾン・ヘルコール」を手札に加える。",
             fn=lambda b: b.hand.append(N("クリムゾン・ヘルコール"))),
        dict(text="ヘルコール①：チェーン・リゾネーターを手札に加える", act="効果", card="クリムゾン・ヘルコール",
             note="フィールドに「レッド・デーモンズ・ドラゴン」の名が記されたＳモンスター（紅蓮の王者）がいるので、デッキのレベル4以下の悪魔族＝チェーン・リゾネーターを手札に加える。",
             fn=lambda b: b.hand.append(N("チェーン・リゾネーター"))),
        dict(text="チェーン・リゾネーター 通常召喚", act="召喚", card="チェーン・リゾネーター",
             note="ダークネス②の追加召喚権で通常召喚。",
             fn=lambda b: (b.drop("チェーン・リゾネーター"), b.mons.append(N("チェーン・リゾネーター")))),
        dict(text="チェーン①：ソウル・リゾネーター 特殊召喚", act="効果", card="チェーン・リゾネーター",
             note="Ｓモンスターがいる状態での召喚成功時に発動（①）。デッキからソウル・リゾネーターを特殊召喚。",
             fn=lambda b: b.mons.append(N("ソウル・リゾネーター"))),
        dict(text="ソウル①：ボーン・デーモンをサーチ", act="効果", card="ソウル・リゾネーター",
             note="デッキからレベル4以下の悪魔族＝ボーン・デーモンを手札に加える。",
             fn=lambda b: b.hand.append(N("ボーン・デーモン"))),
        dict(text="ボーン・デーモン 特殊召喚（コスト: ヘルコール）", act="特殊召喚", card="ボーン・デーモン",
             note="手札のクリムゾン・ヘルコールを墓地へ送って発動（①）。",
             fn=lambda b: (b.gy.append(N("クリムゾン・ヘルコール")),
                           b.drop("クリムゾン・ヘルコール"), b.drop("ボーン・デーモン"),
                           b.mons.append(N("ボーン・デーモン")))),
        dict(text="ボーン②：チューナー（クリムゾン）を墓地へ送る", act="効果", card="ボーン・デーモン",
             note="手札の悪魔族チューナー＝クリムゾン・リゾネーターを墓地へ送る（②コスト）。",
             fn=lambda b: (b.gy.append(N("クリムゾン・リゾネーター")), b.drop("クリムゾン・リゾネーター"))),
        dict(text="ボーン②解決：ボーンのレベルを1下げる（4→3）", act="効果", card="ボーン・デーモン",
             note="対象のボーン・デーモンのレベルを1下げる（②）。ソウル(3)+ボーン(3)＝レベル6の素材が揃う。",
             fn=lambda b: None),
        dict(text="レッド・ライジング・ドラゴン シンクロ（3+3）", act="シンクロ", card="レッド・ライジング・ドラゴン",
             note="ソウル(3)+ボーン(3)でレッド・ライジング・ドラゴン(6)。素材2体は墓地へ。",
             fn=lambda b: (b.gy.extend([N("ソウル・リゾネーター"), N("ボーン・デーモン")]),
                           b.keep(["紅蓮の王者", "チェーン・リゾネーター"]),
                           b.mons.append(N("レッド・ライジング・ドラゴン")))),
        dict(text="ライジング①：墓地のクリムゾン・リゾネーター 特殊召喚", act="効果", card="レッド・ライジング・ドラゴン",
             note="墓地の「リゾネーター」＝クリムゾン・リゾネーターを蘇生（①）。",
             fn=lambda b: b.mons.append(N("クリムゾン・リゾネーター"))),
        dict(text="クリムゾン・ブレード・ドラゴン シンクロ（6+1）", act="シンクロ", card="クリムゾン・ブレード・ドラゴン",
             note="ライジング(6)+チェーン(1)＝7でクリムゾン・ブレード・ドラゴン。素材2体は墓地へ。クリムゾンは場に残す。",
             fn=lambda b: (b.gy.extend([N("レッド・ライジング・ドラゴン"), N("チェーン・リゾネーター")]),
                           b.keep(["紅蓮の王者", "クリムゾン・リゾネーター"]),
                           b.mons.append(N("クリムゾン・ブレード・ドラゴン")))),
        dict(text="クリムゾン②：シンクローン+ダークネス 特殊召喚", act="効果", card="クリムゾン・リゾネーター",
             note="デッキから「リゾネーター」2体＝シンクローン・リゾネーターとダークネス・リゾネーターを特殊召喚（②）。",
             fn=lambda b: (b.mons.append(N("シンクローン・リゾネーター")), b.mons.append(N("ダークネス・リゾネーター")))),
        dict(text="ブレード①：深淵の獣ルベリオンをサーチ", act="効果", card="クリムゾン・ブレード・ドラゴン",
             note="デッキからレベル8以上の通常召喚できないモンスター＝深淵の獣ルベリオンを手札に加える。",
             fn=lambda b: b.hand.append(N("深淵の獣ルベリオン"))),
        dict(text="スカーレッド・ハイパーノヴァ シンクロ（合計12+）", act="シンクロ", card="スカーレッド・ハイパーノヴァ・ドラゴン",
             note="ブレード(7)+クリムゾン(2)+シンクローン(1)+ダークネス(1)+αでスカーレッド・ハイパーノヴァ。素材は全て墓地へ。（※チューナー数の微調整は簡略化）",
             fn=lambda b: (b.gy.extend([N("クリムゾン・ブレード・ドラゴン"), N("クリムゾン・リゾネーター"),
                                        N("シンクローン・リゾネーター"), N("ダークネス・リゾネーター")]),
                           b.keep(["紅蓮の王者"]),
                           b.mons.append(N("スカーレッド・ハイパーノヴァ・ドラゴン")))),
        dict(text="ルベリオンを活用して赤き竜 ケッツァーコアトル（簡略化）", act="特殊召喚", card="赤き竜 ケッツァーコアトル",
             note="手札のルベリオンをリリースの補助に使いつつ赤き竜 ケッツァーコアトルをＳ召喚（※細部は簡略化、Konami DB トーナメント最終盤面）。",
             fn=lambda b: (b.gy.append(N("深淵の獣ルベリオン")), b.drop("深淵の獣ルベリオン"),
                           b.mons.append(N("赤き竜 ケッツァーコアトル")))),
        dict(text="スカーレッド・ゾーン セット", act="セット", card="スカーレッド・ゾーン",
             note="妨害用の魔法・罠を伏せて盤面完成。",
             fn=lambda b: b.spells.append(N("スカーレッド・ゾーン"))),
    ])

    # ===== r2 ソウル・リゾネーター始動（スーパーノヴァ盤面） =====
    r2 = route(["クリムゾン・ヘルガイア", "ヴィジョン・リゾネーター"], [
        dict(text="ソウル・リゾネーター 通常召喚", act="召喚", card="ソウル・リゾネーター",
             note="ターン1の通常召喚。",
             fn=lambda b: b.mons.append(N("ソウル・リゾネーター"))),
        dict(text="ソウル①：ボーン・デーモンをサーチ", act="効果", card="ソウル・リゾネーター",
             note="デッキからレベル4以下の悪魔族＝ボーン・デーモンを手札に加える。",
             fn=lambda b: b.hand.append(N("ボーン・デーモン"))),
        dict(text="ボーン・デーモン 特殊召喚（コスト: クリムゾン・ヘルガイア）", act="特殊召喚", card="ボーン・デーモン",
             note="手札のクリムゾン・ヘルガイアを墓地へ送って自己特殊召喚（①）。",
             fn=lambda b: (b.gy.append(N("クリムゾン・ヘルガイア")),
                           b.drop("クリムゾン・ヘルガイア"), b.drop("ボーン・デーモン"),
                           b.mons.append(N("ボーン・デーモン")))),
        dict(text="ボーン②：デッキのチューナー（クリムゾン）を墓地へ送る", act="効果", card="ボーン・デーモン",
             note="悪魔族チューナー＝デッキのクリムゾン・リゾネーターを墓地へ送る（②コスト）。",
             fn=lambda b: b.gy.append(N("クリムゾン・リゾネーター"))),
        dict(text="ボーン②解決：ボーンのレベルを1下げる（4→3）", act="効果", card="ボーン・デーモン",
             note="ボーン・デーモンのレベルを1下げる（②）。ソウル(3)+ボーン(3)＝レベル6の素材が揃う。",
             fn=lambda b: None),
        dict(text="レッド・ライジング・ドラゴン シンクロ（3+3）", act="シンクロ", card="レッド・ライジング・ドラゴン",
             note="ソウル(3)+ボーン(3)でレッド・ライジング・ドラゴン(6)。素材2体は墓地へ。",
             fn=lambda b: (b.gy.extend([N("ソウル・リゾネーター"), N("ボーン・デーモン")]),
                           b.mons.clear(), b.mons.append(N("レッド・ライジング・ドラゴン")))),
        dict(text="ライジング①：墓地のクリムゾン・リゾネーター 特殊召喚", act="効果", card="レッド・ライジング・ドラゴン",
             note="墓地の「リゾネーター」＝クリムゾン・リゾネーターを蘇生（①）。",
             fn=lambda b: b.mons.append(N("クリムゾン・リゾネーター"))),
        dict(text="クリムゾン②：シンクローン+ダークネス 特殊召喚", act="効果", card="クリムゾン・リゾネーター",
             note="デッキから「リゾネーター」2体＝シンクローン・リゾネーターとダークネス・リゾネーターを特殊召喚（②）。",
             fn=lambda b: (b.mons.append(N("シンクローン・リゾネーター")), b.mons.append(N("ダークネス・リゾネーター")))),
        dict(text="スカーレッド・デーモン シンクロ（6+2）", act="シンクロ", card="スカーレッド・デーモン",
             note="ライジング(6)+手札のヴィジョン(2)でスカーレッド・デーモン(8)。素材2体は墓地へ。クリムゾン・シンクローン・ダークネスは場に残す（スーパーノヴァの素材）。",
             fn=lambda b: (b.gy.extend([N("レッド・ライジング・ドラゴン"), N("ヴィジョン・リゾネーター")]),
                           b.drop("ヴィジョン・リゾネーター"),
                           b.keep(["クリムゾン・リゾネーター", "シンクローン・リゾネーター", "ダークネス・リゾネーター"]),
                           b.mons.append(N("スカーレッド・デーモン")))),
        dict(text="スカーレッド・スーパーノヴァ シンクロ（8+2+1+1）", act="シンクロ", card="スカーレッド・スーパーノヴァ・ドラゴン",
             note="スカーレッド・デーモン(8)+クリムゾン(2)+シンクローン(1)+ダークネス(1)＝12でスカーレッド・スーパーノヴァ。素材は全て墓地へ。",
             fn=lambda b: (b.gy.extend([N("スカーレッド・デーモン"), N("クリムゾン・リゾネーター"),
                                        N("シンクローン・リゾネーター"), N("ダークネス・リゾネーター")]),
                           b.mons.clear(), b.mons.append(N("スカーレッド・スーパーノヴァ・ドラゴン")))),
        dict(text="スカーレッド・ゾーン セット", act="セット", card="スカーレッド・ゾーン",
             note="妨害用の魔法・罠を伏せて盤面完成。",
             fn=lambda b: b.spells.append(N("スカーレッド・ゾーン"))),
    ])

    # ===== r3 ガイア始動（琰魔竜アビス盤面） =====
    r3 = route(["クリムゾン・リゾネーター", "クリムゾン・ヘルガイア"], [
        dict(text="クリムゾン・リゾネーター 自己特殊召喚（①）", act="特殊召喚", card="クリムゾン・リゾネーター",
             note="フィールドにモンスターがいない状態で手札から自己特殊召喚（①）。",
             fn=lambda b: (b.drop("クリムゾン・リゾネーター"), b.mons.append(N("クリムゾン・リゾネーター")))),
        dict(text="クリムゾン②：シンクローン+ダークネス 特殊召喚", act="効果", card="クリムゾン・リゾネーター",
             note="デッキから「リゾネーター」2体＝シンクローン・リゾネーターとダークネス・リゾネーターを特殊召喚（②）。",
             fn=lambda b: (b.mons.append(N("シンクローン・リゾネーター")), b.mons.append(N("ダークネス・リゾネーター")))),
        dict(text="ボーン・デーモン 特殊召喚（コスト: クリムゾン・ヘルガイア）", act="特殊召喚", card="ボーン・デーモン",
             note="手札のクリムゾン・ヘルガイアを墓地へ送って発動（①）でボーン・デーモンを特殊召喚。",
             fn=lambda b: (b.gy.append(N("クリムゾン・ヘルガイア")),
                           b.drop("クリムゾン・ヘルガイア"), b.drop("ボーン・デーモン"),
                           b.mons.append(N("ボーン・デーモン")))),
        dict(text="ボーン②：レベルを1下げる（4→3）", act="効果", card="ボーン・デーモン",
             note="悪魔族チューナー（デッキ2枚目のクリムゾン想定）を墓地へ送り対象のレベルを1下げる（②）。",
             fn=lambda b: b.gy.append(N("クリムゾン・リゾネーター"))),
        dict(text="レッド・デーモンズ・ドラゴン シンクロ（2+1+1+4＝8）", act="シンクロ", card="レッド・デーモンズ・ドラゴン",
             note="クリムゾン(2)+シンクローン(1)+ダークネス(1)+ボーン(4)でレッド・デーモンズ・ドラゴン(8)。クリムゾン・シンクローン・ダークネスは墓地へ。",
             fn=lambda b: (b.gy.extend([N("クリムゾン・リゾネーター"), N("シンクローン・リゾネーター"), N("ダークネス・リゾネーター")]),
                           b.keep(["ボーン・デーモン"]),
                           b.mons.append(N("レッド・デーモンズ・ドラゴン")))),
        dict(text="琰魔竜 レッド・デーモン・アビス シンクロ（8+α）", act="シンクロ", card="琰魔竜 レッド・デーモン・アビス",
             note="レッド・デーモンズ・ドラゴン(8)にチューナー1体（墓地クリムゾンの蘇生想定）を合わせて琰魔竜 レッド・デーモン・アビス。素材は墓地へ。（※素材構成は簡略化）",
             fn=lambda b: (b.mons.clear(), b.mons.append(N("琰魔竜 レッド・デーモン・アビス")))),
        dict(text="スカーレッド・ゾーン セット", act="セット", card="スカーレッド・ゾーン",
             note="妨害用の魔法・罠を伏せて盤面完成。",
             fn=lambda b: b.spells.append(N("スカーレッド・ゾーン"))),
    ])

    # ===== r4 ボーン・デーモン始動（スカーレッド盤面） =====
    r4 = route(["ボーン・デーモン", "ソウル・リゾネーター", "クリムゾン・ヘルガイア"], [
        dict(text="ボーン・デーモン 特殊召喚（コスト: 手札1枚）", act="特殊召喚", card="ボーン・デーモン",
             note="手札のクリムゾン・ヘルガイアを墓地へ送って発動（①）。このターンはドラゴン族・闇属性ＳモンスターしかEXから特殊召喚できない。",
             fn=lambda b: (b.gy.append(N("クリムゾン・ヘルガイア")),
                           b.drop("クリムゾン・ヘルガイア"), b.drop("ボーン・デーモン"),
                           b.mons.append(N("ボーン・デーモン")))),
        dict(text="ボーン②：デッキのチューナー（クリムゾン）を墓地へ送る", act="効果", card="ボーン・デーモン",
             note="悪魔族チューナー＝クリムゾン・リゾネーターを墓地へ送る（②コスト）。",
             fn=lambda b: b.gy.append(N("クリムゾン・リゾネーター"))),
        dict(text="ボーン②解決：ボーンのレベルを1下げる（4→3）", act="効果", card="ボーン・デーモン",
             note="ボーン・デーモンのレベルを1下げる（②）。ソウル(3)+ボーン(3)＝レベル6の素材が揃う。",
             fn=lambda b: None),
        dict(text="ソウル・リゾネーター 通常召喚", act="召喚", card="ソウル・リゾネーター",
             note="ターン1の通常召喚でソウル・リゾネーター(3)を並べる。",
             fn=lambda b: (b.drop("ソウル・リゾネーター"), b.mons.append(N("ソウル・リゾネーター")))),
        dict(text="ソウル①：クリムゾン・ヘルガイアをサーチ", act="効果", card="ソウル・リゾネーター",
             note="デッキからレベル4以下の悪魔族＝クリムゾン・ヘルガイアを手札に加える（②用の2枚目想定）。",
             fn=lambda b: b.hand.append(N("クリムゾン・ヘルガイア"))),
        dict(text="レッド・ライジング・ドラゴン シンクロ（3+3）", act="シンクロ", card="レッド・ライジング・ドラゴン",
             note="ソウル(3)+ボーン(3)でレッド・ライジング・ドラゴン(6)。素材2体は墓地へ。",
             fn=lambda b: (b.gy.extend([N("ソウル・リゾネーター"), N("ボーン・デーモン")]),
                           b.mons.clear(), b.mons.append(N("レッド・ライジング・ドラゴン")))),
        dict(text="ライジング①：墓地のクリムゾン・リゾネーター 特殊召喚", act="効果", card="レッド・ライジング・ドラゴン",
             note="墓地の「リゾネーター」＝クリムゾン・リゾネーターを蘇生（①）。",
             fn=lambda b: b.mons.append(N("クリムゾン・リゾネーター"))),
        dict(text="クリムゾン②：シンクローン+ダークネス 特殊召喚", act="効果", card="クリムゾン・リゾネーター",
             note="デッキから「リゾネーター」2体＝シンクローン・リゾネーターとダークネス・リゾネーターを特殊召喚（②）。",
             fn=lambda b: (b.mons.append(N("シンクローン・リゾネーター")), b.mons.append(N("ダークネス・リゾネーター")))),
        dict(text="スカーレッド・デーモン シンクロ（6+2）", act="シンクロ", card="スカーレッド・デーモン",
             note="場のライジング(6)+クリムゾン(チューナー2)でスカーレッド・デーモン(8)。素材2体は墓地へ。スーパーノヴァまで展開する場合は r2 を参照。",
             fn=lambda b: (b.gy.extend([N("レッド・ライジング・ドラゴン"), N("クリムゾン・リゾネーター")]),
                           b.mons.clear(), b.mons.append(N("スカーレッド・デーモン")))),
        dict(text="スカーレッド・ゾーン セット", act="セット", card="スカーレッド・ゾーン",
             note="妨害用の魔法・罠を伏せて盤面完成（スーパーノヴァまで展開する場合は r2 を参照）。",
             fn=lambda b: b.spells.append(N("スカーレッド・ゾーン"))),
    ])

    metas = [
        {"id": "r1", "name": "パワー・バイス・ドラゴン始動（ハイパーノヴァ/赤き竜）",
         "summary": "パワー・バイス・ドラゴンの自己特殊召喚からダークネス・リゾネーターを絡め、ボーン・デーモン展開でスカーレッド・ハイパーノヴァ＋赤き竜 ケッツァーコアトルまで突き上げる最長ルート。"},
        {"id": "r2", "name": "ソウル・リゾネーター始動（スーパーノヴァ盤面）",
         "summary": "ソウル・リゾネーター×ボーン・デーモンでライジングを展開し、クリムゾンの蘇生効果からシンクローンを絡めてスカーレッド・スーパーノヴァ・ドラゴンまで持っていく基本2ルート。"},
        {"id": "r3", "name": "ガイア始動（琰魔竜アビス盤面）",
         "summary": "クリムゾン・ヘルガイアでクリムゾン・リゾネーターを展開し、琰魔竜 レッド・デーモン・アビスを中心にした妨害母体を作るルート。"},
        {"id": "r4", "name": "ボーン・デーモン始動（スカーレッド盤面）",
         "summary": "手札のボーン・デーモンをコストで特殊召喚し、ソウル・リゾネーターと合わせてレッド・ライジング・ドラゴン経由でスカーレッド・デーモン＋スカーレッド・ゾーン盤面を作る。"},
    ]
    routes_new = []
    for meta, steps_all in zip(metas, (r1, r2, r3, r4)):
        rr = dict(meta)
        rr["steps"] = steps_all
        routes_new.append(rr)

    deck["routes"] = routes_new
    json.dump(deck, open(DECK_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in routes_new:
        print(r["id"], r["name"], "steps:", len(r["steps"]))


if __name__ == "__main__":
    main()
