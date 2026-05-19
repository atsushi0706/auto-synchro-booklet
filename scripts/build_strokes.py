"""kanji データセット(新字体画数)→ 同梱用のコンパクトな {漢字:画数} JSON を生成。

元データ: davidluzgouveia/kanji-data (kanji.json, 新字体/常用準拠の strokes)
出力: data/kanji_strokes.json
"""

import io
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data_strokes_raw.json")
OUT_DIR = os.path.join(ROOT, "data")
OUT = os.path.join(OUT_DIR, "kanji_strokes.json")


def main() -> None:
    with io.open(RAW, encoding="utf-8") as f:
        data = json.load(f)
    table = {k: v["strokes"] for k, v in data.items()
             if isinstance(v.get("strokes"), int)}
    os.makedirs(OUT_DIR, exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(table, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {len(table)} kanji -> {OUT}")


if __name__ == "__main__":
    main()
