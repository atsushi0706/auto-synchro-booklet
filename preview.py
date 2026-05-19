"""mock モードでパイプライン全体を通すドライラン。"""
import io
import sys

sys.path.insert(0, ".")
from sanmei import build_meishiki, build_seimei
from prompts.translate import build_profile
from prompts.chain import generate_booklet

m = build_meishiki(1985, 6, 14)
s = build_seimei("萩村", "日桜璃")
prof = build_profile(m, s)
books = generate_booklet("萩村日桜璃", prof)

out = io.open("preview_out.txt", "w", encoding="utf-8")
out.write("=== 命式(裏ロジック) ===\n")
out.write(str(m.to_dict()) + "\n\n")
out.write("=== 姓名(裏ロジック) ===\n")
out.write(str(s.to_dict()) + "\n\n")
out.write("=== 意識プロファイル(Haiku翻訳) ===\n")
for k, v in prof.items():
    out.write(f"[{k}] {v}\n")
out.write("\n=== 生成冊子(Gemini, mock) ===\n")
for k, v in books.items():
    out.write(f"\n----- {k} -----\n{v}\n")
out.close()
print("preview done")
