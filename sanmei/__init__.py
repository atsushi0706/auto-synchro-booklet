"""算命学エンジン(完全裏ロジック)。

生年月日のみから命式(三柱・蔵干・十大主星・十二大従星)を算出する。
ここで算出した構造化データは、占い用語のまま外に出さず、
prompts 層でオートマチック・シンクロの言葉へ翻訳して使う。
"""

from .meishiki import build_meishiki, Meishiki
from .seimei import build_seimei, Seimei

__all__ = ["build_meishiki", "Meishiki", "build_seimei", "Seimei"]
