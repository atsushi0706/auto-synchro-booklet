"""干支(六十干支)・通日・日柱の基礎ロジック。

日干支は出生時刻を使わない流派に合わせ、暦日(0時切替)で確定する。
基準: 1900-01-01 = 甲戌日(干支序数10) → 検算 2000-01-01 = 戊午(54)。
"""

from __future__ import annotations

# 十干 / 十二支
KAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
SHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 五行・陰陽(十干)
GOGYO_KAN = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
INYO_KAN = {
    "甲": "陽", "乙": "陰", "丙": "陽", "丁": "陰", "戊": "陽",
    "己": "陰", "庚": "陽", "辛": "陰", "壬": "陽", "癸": "陰",
}


def julian_day(year: int, month: int, day: int) -> int:
    """グレゴリオ暦の日付 → ユリウス通日(整数, 正午基準の整数JDN)。"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return (
        day
        + (153 * m + 2) // 5
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )


def kanshi_index(year: int, month: int, day: int) -> int:
    """その暦日の六十干支序数(0=甲子 .. 59=癸亥)。"""
    return (julian_day(year, month, day) + 49) % 60


def kanshi_name(index: int) -> str:
    return KAN[index % 10] + SHI[index % 12]


def day_pillar(year: int, month: int, day: int) -> tuple[str, str]:
    """日柱(日干, 日支)。"""
    idx = kanshi_index(year, month, day)
    return KAN[idx % 10], SHI[idx % 12]


def year_pillar(setsu_year: int) -> tuple[str, str]:
    """年柱。立春で切り替えた後の「年」を渡す。"""
    return KAN[(setsu_year - 4) % 10], SHI[(setsu_year - 4) % 12]


def month_pillar(year_kan: str, month_shi: str) -> tuple[str, str]:
    """月柱。五虎遁(年干から寅月の干を起こす)で月干を決める。"""
    # 寅月の月干: 甲己→丙, 乙庚→戊, 丙辛→庚, 丁壬→壬, 戊癸→甲
    tora_start = {
        "甲": "丙", "己": "丙",
        "乙": "戊", "庚": "戊",
        "丙": "庚", "辛": "庚",
        "丁": "壬", "壬": "壬",
        "戊": "甲", "癸": "甲",
    }
    start_kan_idx = KAN.index(tora_start[year_kan])
    # 寅(2)を起点に、対象の支まで進めた数だけ月干も進む
    steps = (SHI.index(month_shi) - SHI.index("寅")) % 12
    return KAN[(start_kan_idx + steps) % 10], month_shi
