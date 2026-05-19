# Streamlit Community Cloud の既定エントリ名。実体は app.py。
# Main file path を空のままにしても動くようにするためのブリッジ。
import runpy

runpy.run_path("app.py", run_name="__main__")
