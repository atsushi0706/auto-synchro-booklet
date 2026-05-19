# オートマチック・シンクロ｜あなた専用の冊子ジェネレーター

「オートマチック・シンクロ 診断＆勉強会」参加特典の自動生成ツール。
**生年月日 + 氏名** から、3冊の冊子をWebフリップブックで生成する。

1. ① あなた専用の取扱説明書（意識のクセ／シンクロが起きやすいパターン／過去の契約／自分への戻り方）
2. ② あなたに合ったパートナー説明書（人間関係の地図）
3. ③ あなたに合ったお金の引き寄せ説明書（お金との関わり方の指針）

## 設計思想：地面とレンズ

- **裏ロジック（地面）**：算命学（生年月日 → 命式）＋ 姓名判断（氏名 → 五格・陰陽配列）。
  すべて**ローカル計算・APIコストゼロ・再現性100%**。
- **レンズ（表の言葉）**：**Gemini 3.1 Flash-Lite に一本化**。命式・姓名の構造
  データを「意識プロファイル」へ翻訳し、3冊の本文をチェーン生成。
- 別人で出力が同一化しないよう、命式から固有スペック（核となる性質・
  エネルギー量・意識の軸）を決定論で算出し、それが出力を主導する。
- VSLの前提「霊的な話ではない／心理メカニズム」を守るため、
  **占い用語は出力に一切出さない**（`prompts/worldview.py` の禁止リストで強制）。

```
生年月日 ──▶ sanmei.build_meishiki ─┐
                                    ├─▶ Gemini翻訳(意識プロファイル) ─▶ Gemini冊子生成 ─▶ フリップブック
氏名   ──▶ sanmei.build_seimei  ──┘
```

## 構成

| パス | 役割 |
|---|---|
| `sanmei/kanshi.py` | 干支・通日・日柱 |
| `sanmei/setsuiri.py` | 節入り(節気)計算・立春切替 |
| `sanmei/meishiki.py` | 命式(三柱・蔵干・十大主星・十二大従星) |
| `sanmei/seimei.py` | 姓名判断(五格・五行・陰陽配列) |
| `data/kanji_strokes.json` | 同梱画数データ(13,108字・新字体準拠) |
| `prompts/worldview.py` | 世界観・トーン規定・占い用語禁止・翻訳表 |
| `prompts/translate.py` | 翻訳レイヤー(Gemini→意識プロファイル) |
| `prompts/chain.py` | 冊子ライター(Gemini チェーン生成) |
| `app.py` | Streamlit Webフリップブック＋日次上限キャップ |
| `tests/test_sanmei.py` | 算命学エンジン検算 |

## セットアップ

```bash
pip install -r requirements.txt
# 環境変数 / Streamlit secrets を設定
#   GOOGLE_API_KEY     … Gemini APIキー(必須)
#   ASB_DAILY_LIMIT    … 1日の生成回数上限(任意・既定50)
streamlit run app.py
```

任意の環境変数:
`ASB_GEMINI_MODEL`（既定 `gemini-3.1-flash-lite`）/ `ASB_DAILY_LIMIT` /
`ASB_SUPERVISOR_NAME` / `ASB_PRODUCT_NAME` / `ASB_SESSION_NAME`
（監修者・商品名はハードコードしない）。

**APIキー未設定でも mock モードで動作**（プレビュー/dry-run用）。

## デプロイ（Streamlit Community Cloud）

1. このリポジトリ（**非公開可**）を GitHub に push
2. share.streamlit.io → New app → 本リポジトリ / `app.py` を指定
3. Advanced settings → Secrets に下記を貼る（**キーはリポジトリに置かない**）：
   ```toml
   GOOGLE_API_KEY = "（Gemini APIキー）"
   ASB_DAILY_LIMIT = "50"
   ```
4. Deploy。`app.py` が Streamlit secrets を環境変数へ橋渡しする。

**課金注意**：Gemini が無料枠のままだと 1 日 20 リクエストで停止する
（1 生成＝4 リクエスト）。実運用は対象 Google プロジェクトで
**請求を有効化**すること。暴走防止に日次上限キャップを内蔵。

## 既知の前提・制約

- 画数は **新字体（常用準拠）**。旧字体（康熙字典）流派とは結果が異なる。
  出力にもその旨を明記している（事実でないことは書かない方針）。
- 節入りは簡略式（1900–2099, JST近似）。当日±1日は誤差帯のため
  `boundary_warning` を立て、生成側で断定を避ける。
- 算命学は出生時刻を使わない流派に合わせ、日干支は暦日(0時切替)で確定。

## 検算

```bash
python tests/test_sanmei.py
```
