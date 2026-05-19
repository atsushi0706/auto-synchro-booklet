"""姓名判断(決定論パート)。

画数は同梱データ(新字体/常用準拠)で算出する。流派により旧字体(康熙字典)
画数を用いる場合があるが、本実装は再現性を優先し新字体基準。出力にその旨を
明記すること(嘘を書かない)。

ここで出すのは内部構造データ(五格・五行・陰陽配列)のみ。
意味づけ・解釈は Haiku 翻訳レイヤーが担当する。
"""

from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass, asdict

_DATA = os.path.join(os.path.dirname(__file__), "..", "data", "kanji_strokes.json")
with io.open(_DATA, encoding="utf-8") as _f:
    _KANJI_STROKES: dict[str, int] = json.load(_f)

# かな画数(姓名判断の慣用表)。拗音・促音は基字の画数で数える流派を採用。
_KANA = {
    "あ": 3, "い": 2, "う": 2, "え": 3, "お": 3, "か": 3, "き": 4, "く": 1,
    "け": 3, "こ": 2, "さ": 3, "し": 1, "す": 2, "せ": 3, "そ": 3, "た": 4,
    "ち": 3, "つ": 1, "て": 2, "と": 2, "な": 5, "に": 4, "ぬ": 4, "ね": 4,
    "の": 1, "は": 4, "ひ": 2, "ふ": 4, "へ": 1, "ほ": 4, "ま": 4, "み": 3,
    "む": 6, "め": 2, "も": 3, "や": 3, "ゆ": 3, "よ": 3, "ら": 3, "り": 2,
    "る": 2, "れ": 3, "ろ": 2, "わ": 3, "ゐ": 4, "ゑ": 5, "を": 4, "ん": 2,
    "が": 5, "ぎ": 6, "ぐ": 3, "げ": 5, "ご": 4, "ざ": 5, "じ": 3, "ず": 4,
    "ぜ": 5, "ぞ": 5, "だ": 6, "ぢ": 5, "づ": 3, "で": 4, "ど": 4, "ば": 5,
    "び": 3, "ぶ": 5, "べ": 2, "ぼ": 5, "ぱ": 5, "ぴ": 3, "ぷ": 5, "ぺ": 2,
    "ぽ": 5, "ゃ": 3, "ゅ": 3, "ょ": 3, "っ": 1, "ぁ": 3, "ぃ": 2, "ぅ": 2,
    "ぇ": 3, "ぉ": 3, "ー": 1, "ゔ": 5,
}
# カタカナはひらがなへ写像して同じ画数表を使う
_KATA_OFFSET = ord("ァ") - ord("ぁ")

# 格数の末尾 → 五行(1,2木 3,4火 5,6土 7,8金 9,0水)
_GOGYO_BY_DIGIT = {1: "木", 2: "木", 3: "火", 4: "火", 5: "土",
                   6: "土", 7: "金", 8: "金", 9: "水", 0: "水"}


def _char_strokes(ch: str) -> int | None:
    if ch in _KANJI_STROKES:
        return _KANJI_STROKES[ch]
    if ch in _KANA:
        return _KANA[ch]
    # カタカナ → ひらがな化
    if "ァ" <= ch <= "ヴ":
        h = chr(ord(ch) - _KATA_OFFSET)
        if h in _KANA:
            return _KANA[h]
    return None


def _strokes_list(s: str) -> list[int]:
    out = []
    for ch in s:
        n = _char_strokes(ch)
        if n is None:
            raise ValueError(f"画数を特定できない文字: '{ch}' (旧字体や異体字は未対応)")
        out.append(n)
    return out


def _gogyo(num: int) -> str:
    return _GOGYO_BY_DIGIT[num % 10]


@dataclass
class Seimei:
    sei: str
    mei: str
    sei_strokes: list[int]
    mei_strokes: list[int]
    tenkaku: int      # 天格(姓の合計)
    jinkaku: int      # 人格(姓の末字+名の頭字) … 性格の中心
    chikaku: int      # 地格(名の合計)
    gaikaku: int      # 外格(対人)
    soukaku: int      # 総格(総合・晩年)
    sansai: tuple     # 三才(天・人・地の五行)
    inyo_pattern: str  # 例: "○●○○" (奇数画=陽○ / 偶数画=陰●)
    inyo_type: str     # all_yang / all_yin / balanced / biased
    stroke_basis: str = "新字体(常用準拠)"

    def to_dict(self) -> dict:
        return asdict(self)


def _inyo_type(pattern: str) -> str:
    if set(pattern) == {"○"}:
        return "all_yang"
    if set(pattern) == {"●"}:
        return "all_yin"
    y, i = pattern.count("○"), pattern.count("●")
    return "balanced" if abs(y - i) <= 1 else "biased"


def build_seimei(sei: str, mei: str) -> Seimei:
    sei = sei.strip()
    mei = mei.strip()
    if not sei or not mei:
        raise ValueError("姓と名の両方を入力してください")

    ss = _strokes_list(sei)
    ms = _strokes_list(mei)

    tenkaku = sum(ss)
    chikaku = sum(ms)
    jinkaku = ss[-1] + ms[0]
    soukaku = tenkaku + chikaku
    # 外格: 総格 - 人格。1字姓/1字名は霊数1を補う慣用に合わせる。
    if len(ss) == 1 and len(ms) == 1:
        gaikaku = 2
    elif len(ss) == 1 or len(ms) == 1:
        gaikaku = soukaku - jinkaku + 1
    else:
        gaikaku = soukaku - jinkaku

    pattern = "".join("○" if n % 2 else "●" for n in (ss + ms))

    return Seimei(
        sei=sei, mei=mei,
        sei_strokes=ss, mei_strokes=ms,
        tenkaku=tenkaku, jinkaku=jinkaku, chikaku=chikaku,
        gaikaku=gaikaku, soukaku=soukaku,
        sansai=(_gogyo(tenkaku), _gogyo(jinkaku), _gogyo(chikaku)),
        inyo_pattern=pattern,
        inyo_type=_inyo_type(pattern),
    )
