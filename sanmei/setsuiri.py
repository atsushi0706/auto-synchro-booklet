"""節入り(二十四節気のうち「節」)の日付計算。

外部API・天文ライブラリに依存しない簡略式(1900-2099, JST近似)を用いる。
精度は通常 ±0 日、節入り当日付近のみ ±1 日の不確実性が残るため、
is_near_boundary() で境界を検出し、生成側で「断定しない」表現に回す。
"""

from __future__ import annotations

# 二十四節気の順序(小寒=0 .. 冬至=23)。「節」は偶数インデックス。
TERMS = [
    "小寒", "大寒", "立春", "雨水", "啓蟄", "春分",
    "清明", "穀雨", "立夏", "小満", "芒種", "夏至",
    "小暑", "大暑", "立秋", "処暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
]

# 月支は「節」で切り替わる(立春→寅月, 啓蟄→卯月, ...)
SETSU_TO_SHI = {
    "立春": "寅", "啓蟄": "卯", "清明": "辰", "立夏": "巳",
    "芒種": "午", "小暑": "未", "立秋": "申", "白露": "酉",
    "寒露": "戌", "立冬": "亥", "大雪": "子", "小寒": "丑",
}

# century 定数(C)。index は TERMS と対応。
_C19 = [
    6.11, 20.84, 4.6295, 19.4599, 6.3826, 21.4155,
    5.59, 20.888, 6.318, 21.86, 6.5, 22.20,
    7.928, 23.65, 8.35, 23.95, 8.44, 23.822,
    9.098, 24.218, 8.218, 23.08, 7.9, 22.60,
]
_C20 = [
    5.4055, 20.12, 3.87, 18.73, 5.63, 20.646,
    4.81, 20.1, 5.52, 21.04, 5.678, 21.37,
    7.108, 22.83, 7.5, 23.13, 7.646, 23.042,
    8.318, 23.438, 7.438, 22.36, 7.18, 21.94,
]

# 簡略式が外す既知年の補正(年, 節気index)->補正日数。テストで実証して追加。
_EXCEPTIONS: dict[tuple[int, int], int] = {
    (2026, 2): 0,
}

_MONTH_OF_TERM = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6,
                  7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12]


def term_day(year: int, term_index: int) -> int:
    """その年の指定節気の「日」を返す(月は _MONTH_OF_TERM で決まる)。

    世紀境界の取り違えを避けるため %100 ではなく基準年差分で計算する。
    1900-2000 は 1900 基準(2000 は Y=100)、2001-2099 は 2000 基準。
    """
    if year <= 2000:
        C, Y = _C19[term_index], year - 1900
    else:
        C, Y = _C20[term_index], year - 2000
    # 小寒・大寒・立春・雨水(1-2月)は当年の閏日(2/29)前なので (Y-1)//4
    leap = (Y - 1) // 4 if term_index in (0, 1, 2, 3) else Y // 4
    d = int(C + 0.2422 * Y - leap)
    return d + _EXCEPTIONS.get((year, term_index), 0)


def term_date(year: int, term_index: int) -> tuple[int, int, int]:
    return year, _MONTH_OF_TERM[term_index], term_day(year, term_index)


def _ymd_key(y: int, m: int, d: int) -> int:
    return y * 10000 + m * 100 + d


def pillar_year(year: int, month: int, day: int) -> int:
    """立春で切り替えた「年柱用の年」。"""
    ry, rm, rd = term_date(year, 2)  # 立春
    if _ymd_key(year, month, day) < _ymd_key(ry, rm, rd):
        return year - 1
    return year


def month_branch(year: int, month: int, day: int) -> str:
    """その日が属する「節」から月支を決める。"""
    key = _ymd_key(year, month, day)
    setsu_indices = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
    current = "丑"  # 小寒〜立春前は丑月(前年12月節〜)
    found = None
    for ti in setsu_indices:
        ty, tm, td = term_date(year, ti)
        if key >= _ymd_key(ty, tm, td):
            found = TERMS[ti]
    if found and found in SETSU_TO_SHI:
        current = SETSU_TO_SHI[found]
    elif found == "小寒":
        current = "丑"
    # 1月で小寒前(=前年大雪節の子月)
    if month == 1:
        sy, sm, sd = term_date(year, 0)  # 小寒
        if key < _ymd_key(sy, sm, sd):
            current = "子"
    return current


def is_near_boundary(year: int, month: int, day: int) -> bool:
    """節入り当日±1日なら True(±1日の計算誤差リスク帯)。"""
    for ti in range(24):
        ty, tm, td = term_date(year, ti)
        if tm == month and abs(td - day) <= 1:
            return True
    return False
