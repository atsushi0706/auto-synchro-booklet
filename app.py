"""オートマチック・シンクロ 冊子ジェネレーター(Webフリップブック)。

生年月日 + 氏名 → 算命学/姓名判断(裏ロジック) → Haiku翻訳 →
Gemini冊子生成 → ページめくり表示。占い用語は表に出さない。
"""

import base64
import datetime as dt
import json
import os

import streamlit as st

from sanmei import build_meishiki, build_seimei
from prompts.translate import build_profile
from prompts.chain import generate_booklet
from prompts.worldview import PRODUCT_NAME, SESSION_NAME

st.set_page_config(page_title=f"{PRODUCT_NAME} 冊子", page_icon="📖",
                   layout="centered")

# Streamlit Cloud は秘密情報を st.secrets に入れる(os.getenv には来ない)。
# ローカルは環境変数。両対応のため st.secrets を環境変数へ橋渡しする。
try:
    for _k in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_AI_KEY",
               "ASB_DAILY_LIMIT"):
        if _k not in os.environ and _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

# 課金保護: 1日の合計生成回数に上限を設ける(流出時の暴走を鈍器で止める)。
_USAGE = os.path.join(os.path.dirname(__file__), "data", ".usage.json")


def _daily_limit() -> int:
    try:
        return int(os.getenv("ASB_DAILY_LIMIT", "50"))
    except ValueError:
        return 50


def _usage_today() -> int:
    today = dt.date.today().isoformat()
    try:
        with open(_USAGE, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("count", 0) if d.get("date") == today else 0
    except Exception:
        return 0


def _bump_usage() -> None:
    today = dt.date.today().isoformat()
    try:
        with open(_USAGE, "w", encoding="utf-8") as f:
            json.dump({"date": today, "count": _usage_today() + 1}, f)
    except Exception:
        pass

st.markdown("""
<style>
.book-paper{background:#fbf7ef;border:1px solid #e3d8c3;border-radius:10px;
 padding:38px 44px;box-shadow:0 8px 28px rgba(80,60,30,.15);
 font-family:"Hiragino Mincho ProN","Yu Mincho",serif;line-height:1.95;
 color:#2c2622;min-height:460px;}
.book-paper h1{font-size:1.5rem;border-bottom:2px solid #d8c7a6;
 padding-bottom:.4em;}
.book-paper h2{font-size:1.15rem;color:#6b4f2a;margin-top:1.4em;}
.page-no{text-align:center;color:#9b8a6a;font-size:.85rem;margin-top:6px;}
.notice{background:#f3eee2;border-left:4px solid #c9b481;padding:10px 14px;
 font-size:.82rem;color:#6b5d44;border-radius:4px;}
.cover-wrap{position:relative;border-radius:10px;overflow:hidden;
 box-shadow:0 8px 28px rgba(80,60,30,.18);}
.cover-wrap img{display:block;width:100%;}
.cover-text{position:absolute;inset:0;display:flex;flex-direction:column;
 align-items:center;justify-content:center;text-align:center;
 font-family:"Hiragino Mincho ProN","Yu Mincho",serif;color:#5a4424;}
.cover-text .sub{font-size:.9rem;letter-spacing:.3em;color:#8a7038;
 margin-bottom:1.2em;}
.cover-text .name{font-size:1.5rem;letter-spacing:.16em;color:#6b4f2a;
 margin-bottom:.9em;}
.cover-text .name small{font-size:.62em;letter-spacing:.1em;color:#8a7038;}
.cover-text .theme{font-size:3.1rem;letter-spacing:.14em;color:#5a4424;
 margin:.1em 0 .5em;font-weight:600;}
.cover-text .ttl{font-size:1.0rem;letter-spacing:.2em;color:#6b4f2a;}
.cover-text .foot{position:absolute;bottom:7%;font-size:.76rem;
 letter-spacing:.2em;color:#9b8a6a;}
</style>
""", unsafe_allow_html=True)


def _cover_src() -> str:
    """固定表紙画像(data/cover.* 優先、無ければ同梱SVG)を data URI で返す。"""
    base = os.path.join(os.path.dirname(__file__), "data")
    for ext in ("png", "jpg", "jpeg"):
        p = os.path.join(base, f"cover.{ext}")
        if os.path.exists(p):
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/{ext};base64,{b64}"
    with open(os.path.join(base, "cover.svg"), encoding="utf-8") as f:
        b64 = base64.b64encode(f.read().encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def _cover_html(name: str, theme: str, subtitle: str) -> str:
    """テーマ別の表紙(同一デザイン)。氏名・テーマ語・冊子名を重ねる。"""
    return f"""<div class='cover-wrap'>
  <img src='{_cover_src()}' alt='表紙'/>
  <div class='cover-text'>
    <div class='sub'>{PRODUCT_NAME}</div>
    <div class='name'>{name} さん<small>にとっての</small></div>
    <div class='theme'>「{theme}」</div>
    <div class='ttl'>{subtitle}</div>
    <div class='foot'>{SESSION_NAME} 参加特典</div>
  </div>
</div>"""


BOOKLETS = [
    {"key": "book1", "tab": "① 取扱説明書", "theme": "取り扱い",
     "subtitle": "あなた専用の取扱説明書"},
    {"key": "book2", "tab": "② パートナー", "theme": "パートナー",
     "subtitle": "あなたに合ったパートナー説明書"},
    {"key": "book3", "tab": "③ お金", "theme": "お金",
     "subtitle": "あなたに合ったお金の引き寄せ説明書"},
]

st.title(f"📖 {PRODUCT_NAME}｜あなた専用の冊子")
st.caption(f"{SESSION_NAME} ご参加特典 / 生年月日と氏名から自動生成")

today = dt.date.today()
with st.form("input"):
    c1, c2 = st.columns(2)
    sei = c1.text_input("姓", placeholder="例: 萩村")
    mei = c2.text_input("名", placeholder="例: 日桜璃")
    st.markdown("**生年月日**")
    d1, d2, d3 = st.columns(3)
    years = list(range(today.year, 1899, -1))
    by = d1.selectbox("年", years, index=years.index(1990),
                      format_func=lambda x: f"{x}年")
    bm = d2.selectbox("月", list(range(1, 13)),
                      format_func=lambda x: f"{x}月")
    bd = d3.selectbox("日", list(range(1, 32)),
                      format_func=lambda x: f"{x}日")
    go = st.form_submit_button("冊子を生成する", type="primary",
                               use_container_width=True)
    st.caption("※画数は新字体(常用準拠)で算出します。"
               "旧字体の流派とは結果が異なる場合があります。")

if go:
    if not sei.strip() or not mei.strip():
        st.error("姓と名の両方を入力してください。")
        st.stop()
    try:
        bday = dt.date(by, bm, bd)
    except ValueError:
        st.error(f"{by}年{bm}月{bd}日 は存在しない日付です。確認してください。")
        st.stop()
    if bday > today:
        st.error("生年月日が未来の日付になっています。")
        st.stop()
    if _usage_today() >= _daily_limit():
        st.warning("本日の生成上限に達しました。申し訳ありませんが、"
                   "また明日お試しください。")
        st.stop()
    try:
        with st.spinner("意識の構えを読み解いています…"):
            m = build_meishiki(bday.year, bday.month, bday.day)
            s = build_seimei(sei, mei)
        with st.spinner("あなたの言葉へ翻訳しています…"):
            profile = build_profile(m, s)
        with st.spinner("冊子を綴じています…(3冊を順に執筆)"):
            books = generate_booklet(f"{sei}{mei}", profile)
        _bump_usage()
    except ValueError as e:
        st.error(str(e))
        st.stop()

    st.session_state["books"] = books
    st.session_state["name"] = f"{sei}{mei}"
    st.session_state["boundary"] = m.boundary_warning
    for b in BOOKLETS:  # 再生成時は各冊子を表紙に戻す
        st.session_state[f"pg_{b['key']}"] = False

if "books" in st.session_state:
    books = st.session_state["books"]
    name = st.session_state.get("name", "")

    tabs = st.tabs([b["tab"] for b in BOOKLETS])
    for tab, b in zip(tabs, BOOKLETS):
        with tab:
            pkey = f"pg_{b['key']}"
            opened = st.session_state.get(pkey, False)

            if not opened:  # 表紙(テーマ別・同一デザイン)
                st.markdown(_cover_html(name, b["theme"], b["subtitle"]),
                            unsafe_allow_html=True)
                if st.button("📖 中を読む", key=f"open_{b['key']}",
                             type="primary", use_container_width=True):
                    st.session_state[pkey] = True
                    st.rerun()
            else:  # 本文
                st.markdown(
                    f"<div class='book-paper'>\n\n{books[b['key']]}\n\n</div>",
                    unsafe_allow_html=True)
                st.markdown(
                    f"<div class='page-no'>— {b['subtitle']} —</div>",
                    unsafe_allow_html=True)
                if st.button("← 表紙に戻る", key=f"close_{b['key']}",
                             use_container_width=True):
                    st.session_state[pkey] = False
                    st.rerun()

    if st.session_state.get("boundary"):
        st.markdown("<div class='notice'>※生まれた日が季節の変わり目の"
                    "境目付近です。一部の傾向は幅を持たせて綴じています。"
                    "</div>", unsafe_allow_html=True)
else:
    st.info("上の入力欄に姓・名・生年月日を入れて「冊子を生成する」を"
            "押してください。")
