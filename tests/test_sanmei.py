"""算命学エンジンの検算。決定論バックボーン(日干支・立春切替・月支)を中心に。"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sanmei.kanshi import kanshi_index, kanshi_name, day_pillar  # noqa: E402
from sanmei.setsuiri import term_date, pillar_year, month_branch  # noqa: E402
from sanmei.meishiki import build_meishiki  # noqa: E402


def check(label, got, expected):
    ok = got == expected
    print(f"[{'OK ' if ok else 'NG '}] {label}: got={got} expected={expected}")
    return ok


def main() -> int:
    fails = 0

    # --- 日干支アンカー ---
    fails += not check("1900-01-01 干支序数", kanshi_index(1900, 1, 1), 10)
    fails += not check("1900-01-01 干支名", kanshi_name(kanshi_index(1900, 1, 1)), "甲戌")
    fails += not check("2000-01-01 干支名", kanshi_name(kanshi_index(2000, 1, 1)), "戊午")
    fails += not check("2000-01-01 日柱", day_pillar(2000, 1, 1), ("戊", "午"))

    # --- 立春日(JST, 既知) ---
    for y, expected in [
        (2000, (2000, 2, 4)),
        (2021, (2021, 2, 3)),
        (2022, (2022, 2, 4)),
        (2024, (2024, 2, 4)),
        (2025, (2025, 2, 3)),
        (1985, (1985, 2, 4)),
        (1990, (1990, 2, 4)),
    ]:
        fails += not check(f"{y} 立春", term_date(y, 2), expected)

    # --- 立春での年柱切替 ---
    fails += not check("2024-02-03 は前年扱い", pillar_year(2024, 2, 3), 2023)
    fails += not check("2024-02-04 は当年扱い", pillar_year(2024, 2, 4), 2024)
    fails += not check("2024-12-31 は当年扱い", pillar_year(2024, 12, 31), 2024)

    # --- 月支(節切替) ---
    fails += not check("2024-02-10 は寅月", month_branch(2024, 2, 10), "寅")
    fails += not check("2024-01-20 は丑月", month_branch(2024, 1, 20), "丑")
    fails += not check("2024-12-25 は子月", month_branch(2024, 12, 25), "子")

    # --- 命式が一通り組めるか ---
    m = build_meishiki(1988, 7, 21)
    print("sample 1988-07-21 ->", m.to_dict())
    fails += not check("命式 三柱が干支2文字",
                       all(len(p) == 2 for p in
                           [m.year_pillar, m.month_pillar, m.day_pillar]), True)

    print(f"\n{'ALL PASS' if fails == 0 else str(fails) + ' FAIL'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
