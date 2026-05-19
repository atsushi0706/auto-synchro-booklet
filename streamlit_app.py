# Streamlit Community Cloud の既定エントリ名。実体は app.py。
# Cloud 上で sanmei/prompts パッケージと data/ 相対パスを確実に解決させるため、
# リポジトリ直下を sys.path/cwd に固定してから app.py を実行する。
# (runpy 経由だと import パスが通らず ImportError になるため exec 方式)
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
os.chdir(_HERE)

with open(os.path.join(_HERE, "app.py"), encoding="utf-8") as _f:
    exec(compile(_f.read(), "app.py", "exec"))
