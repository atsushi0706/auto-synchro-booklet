"""命式の組み立て。

三柱(年・月・日) + 蔵干 + 十大主星(通変) + 十二大従星(十二運)。
出力はあくまで内部構造データ。占い用語のまま外へ出さない。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

from .kanshi import (
    KAN, SHI, GOGYO_KAN, INYO_KAN,
    day_pillar, year_pillar, month_pillar,
)
from .setsuiri import pillar_year, month_branch, is_near_boundary

# 各支の本気蔵干(主たる蔵干)
HONKI_ZOKAN = {
    "子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙",
    "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬",
}

# 五行 相生(生む) / 相剋(剋す)
_SEI = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KOKU = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 十大主星(算命学呼称)。四柱の通変に対応。
_SHUSEI = {
    "比肩": "貫索星", "劫財": "石門星",
    "食神": "鳳閣星", "傷官": "調舒星",
    "偏財": "禄存星", "正財": "司禄星",
    "偏官": "車騎星", "正官": "牽牛星",
    "偏印": "龍高星", "印綬": "玉堂星",
}

# 十二大従星(算命学呼称)。十二運に対応。
_JUSEI = {
    "長生": "天貴星", "沐浴": "天恍星", "冠帯": "天南星", "建禄": "天禄星",
    "帝旺": "天将星", "衰": "天堂星", "病": "天胡星", "死": "天極星",
    "墓": "天庫星", "絶": "天馳星", "胎": "天報星", "養": "天印星",
}
_UNSEI_ORDER = ["長生", "沐浴", "冠帯", "建禄", "帝旺", "衰",
                "病", "死", "墓", "絶", "胎", "養"]
# 各日干の長生の支
_CHOSEI_SHI = {
    "甲": "亥", "乙": "午", "丙": "寅", "丁": "酉", "戊": "寅",
    "己": "酉", "庚": "巳", "辛": "子", "壬": "申", "癸": "卯",
}


def _tsuhen(nikkan: str, target_kan: str) -> str:
    """日干から見た target_kan の通変星(算命学呼称)。"""
    dg, tg = GOGYO_KAN[nikkan], GOGYO_KAN[target_kan]
    same_inyo = INYO_KAN[nikkan] == INYO_KAN[target_kan]
    if dg == tg:
        key = "比肩" if same_inyo else "劫財"
    elif _SEI[dg] == tg:          # 日干が生む = 漏らす
        key = "食神" if same_inyo else "傷官"
    elif _KOKU[dg] == tg:         # 日干が剋す = 財
        key = "偏財" if same_inyo else "正財"
    elif _KOKU[tg] == dg:         # 相手が日干を剋す = 官殺
        key = "偏官" if same_inyo else "正官"
    else:                          # 相手が日干を生む = 印
        key = "偏印" if same_inyo else "印綬"
    return _SHUSEI[key]


def _junisei(nikkan: str, shi: str) -> str:
    """日干 × 支 の十二大従星(算命学呼称)。陽干は順行・陰干は逆行。"""
    start = SHI.index(_CHOSEI_SHI[nikkan])
    forward = INYO_KAN[nikkan] == "陽"
    diff = (SHI.index(shi) - start) % 12 if forward else (start - SHI.index(shi)) % 12
    return _JUSEI[_UNSEI_ORDER[diff]]


@dataclass
class Meishiki:
    year: int
    month: int
    day: int
    year_pillar: str          # 例: 甲子
    month_pillar: str
    day_pillar: str
    nikkan: str               # 日干(命式の主体)
    nikkan_gogyo: str
    nikkan_inyo: str
    main_stars: dict          # 年/月/日支 → 十大主星
    body_stars: dict          # 年/月/日支 → 十二大従星
    boundary_warning: bool    # 節入り境界(±1日)の不確実性

    def to_dict(self) -> dict:
        return asdict(self)


def build_meishiki(year: int, month: int, day: int) -> Meishiki:
    py = pillar_year(year, month, day)
    yk, ys = year_pillar(py)
    msh = month_branch(year, month, day)
    mk, ms = month_pillar(yk, msh)
    dk, ds = day_pillar(year, month, day)

    main_stars = {
        "年": _tsuhen(dk, HONKI_ZOKAN[ys]),
        "月": _tsuhen(dk, HONKI_ZOKAN[ms]),
        "日": _tsuhen(dk, HONKI_ZOKAN[ds]),
    }
    body_stars = {
        "年": _junisei(dk, ys),
        "月": _junisei(dk, ms),
        "日": _junisei(dk, ds),
    }
    return Meishiki(
        year=year, month=month, day=day,
        year_pillar=yk + ys,
        month_pillar=mk + ms,
        day_pillar=dk + ds,
        nikkan=dk,
        nikkan_gogyo=GOGYO_KAN[dk],
        nikkan_inyo=INYO_KAN[dk],
        main_stars=main_stars,
        body_stars=body_stars,
        boundary_warning=is_near_boundary(year, month, day),
    )
