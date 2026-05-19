"""翻訳レイヤー(Claude Haiku)。

命式・姓名判断を、その人“固有”の意識プロファイルへ翻訳する。
別人が同じ文章になることを構造的に防ぐため、決定論的に算出した
固有の特徴(日干の質・核となる主星・エネルギー量・意識の軸・陰陽)を
スペックとして渡し、Haiku にはそれを必ず反映させる。
"""

from __future__ import annotations

import json

from sanmei import Meishiki, Seimei
from .llm import gemini
from .worldview import (
    WORLDVIEW, TONE, banned_terms_clause,
    NIKKAN_NATURE, STAR_NATURE, BODY_ENERGY_DESC,
    INYO_TYPE_NOTE, energy_total, energy_profile,
)

_SYS = WORLDVIEW + "\n" + TONE + "\n" + banned_terms_clause()

_KEYS = [
    "意識の核", "強み", "意識のクセ", "シンクロ率の傾向",
    "シンクロが起きやすい場面", "過去の契約の傾向", "自分への戻り方",
    "お金との関わり方のクセ", "意識が戻ると変わること", "引き寄せの整え方",
    "飛びやすい相手", "自分を保てる相手", "関わり方の処方箋",
    "名前が強める癖",
]


def _spec(m: Meishiki, s: Seimei) -> str:
    """別人で絶対に同一化しない、固有の決定論スペックを組む。"""
    core = STAR_NATURE[m.main_stars["月"]]   # 性質の核は月主星
    sub = STAR_NATURE[m.main_stars["日"]]    # 内面・身近は日主星
    soc = STAR_NATURE[m.main_stars["年"]]    # 社会面は年主星
    total = energy_total(m.body_stars)
    en = energy_profile(total)
    inyo = INYO_TYPE_NOTE.get(s.inyo_type, "")
    near = ("生まれた日が季節の変わり目付近のため、核となる性質は"
            "断定せず2方向の幅を持たせて書くこと。"
            if m.boundary_warning else "")

    spec = {
        "意識の主体の地の質": NIKKAN_NATURE[m.nikkan],
        "核となる性質(最重要)": core["core"],
        "本来の強み": f"{core['strength']}／{sub['strength']}",
        "内面・身近での出方": sub["core"],
        "社会・対外での出方": soc["core"],
        "意識の軸": core["axis"],
        "お金との関わりの素地": core["money"],
        "エネルギー量": f"{en['level']}(内部値{total}/36)",
        "エネルギーの質": "・".join(
            BODY_ENERGY_DESC[v] for v in m.body_stars.values()),
        "シンクロ率の傾向": en["synchro"],
        "自分軸か同調かの傾向": en["note"],
        "名前から受ける偏り": inyo,
        "境界注意": near,
    }
    return json.dumps(spec, ensure_ascii=False, indent=2)


def build_profile(m: Meishiki, s: Seimei) -> dict:
    """Haiku で“その人固有”の意識プロファイルを生成。"""
    spec = _spec(m, s)
    schema = ",\n".join(f'  "{k}": "..."' for k in _KEYS)
    prompt = f"""次は【この人だけ】の意識の構えを内部解析した確定スペックです。
占いの結果ではなく、生まれ持った意識傾向と名前のエネルギーを
心理メカニズムとして言語化するための“動かせない素材”です。

== 確定スペック(この人固有・必ず反映) ==
{spec}

厳守事項:
- 上のスペックを唯一の根拠にする。スペックに無い人物像を足さない。
- 「優しい/気が利く/本音を飲み込む自己犠牲の人」を既定値にしない。
  スペックの『意識の軸』が自分軸なら、自分軸の人として書く。
- 別人なら全く違う文章になるはず。核となる性質・エネルギー量・軸を
  具体的に効かせ、その人固有の像を立てる。
- お金との関わりは『お金との関わりの素地』と『意識の軸』から導く。
  “誰かのために稼いできた”等を全員に当てはめてはならない。
{TONE}
占い・運勢・スピリチュアルの語は一切使わない。
次の JSON だけを出力(各値は日本語2〜4文、上のスペックと矛盾させない):

{{
{schema}
}}"""
    raw = gemini(_SYS, prompt, max_tokens=2600)
    return _safe_json(raw, fallback_keys=_KEYS)


def _safe_json(raw: str, fallback_keys: list[str]) -> dict:
    txt = raw.strip()
    if "```" in txt:
        txt = txt.split("```")[1].lstrip("json").strip()
    start, end = txt.find("{"), txt.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(txt[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {k: raw for k in fallback_keys}  # 失敗時も生テキストを温存
