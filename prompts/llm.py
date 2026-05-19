"""LLM クライアント(薄いラッパ)。

- 翻訳レイヤー: Claude Haiku(ユーザー提供キー)。構造データの判断・翻訳に使う。
- 冊子ライター: Gemini Flash(既存ツールと統一)。長文の執筆に使う。
キーが無い場合は mock モードで動く(プレビュー/dry-run 用)。
"""

from __future__ import annotations

import os
import time


def _retry(fn, tries: int = 4, base: float = 2.0):
    """503/一時エラー向けの指数バックオフ。最後は例外を送出。"""
    for n in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            transient = ("503" in msg or "UNAVAILABLE" in msg
                         or "overloaded" in msg or "429" in msg)
            if not transient or n == tries - 1:
                raise
            time.sleep(base * (2 ** n))

HAIKU_MODEL = os.getenv("ASB_HAIKU_MODEL", "claude-haiku-4-5-20251001")
GEMINI_MODEL = os.getenv("ASB_GEMINI_MODEL", "gemini-3.1-flash-lite")


def _have_anthropic() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _have_gemini() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_AI_KEY"))


def haiku(system: str, prompt: str, max_tokens: int = 1500) -> str:
    """Claude Haiku で構造データを翻訳・判断する。"""
    if not _have_anthropic():
        # Gemini があればフォールバック、無ければ mock
        if _have_gemini():
            return gemini(system, prompt, max_tokens)
        return _mock("HAIKU", prompt)
    import anthropic

    client = anthropic.Anthropic()
    # プロンプトキャッシュ: 共通の世界観/規定を system に置きキャッシュ
    msg = _retry(lambda: client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    ))
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def gemini(system: str, prompt: str, max_tokens: int = 4000) -> str:
    """Gemini Flash で冊子の本文を執筆する。"""
    if not _have_gemini():
        if _have_anthropic():
            return haiku(system, prompt, max_tokens)
        return _mock("GEMINI", prompt)
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_AI_KEY")
    )
    resp = _retry(lambda: client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=0.8,
            # 冊子執筆に推論は不要。thinking を切り、出力トークンを
            # 本文に全振り(コスト・末尾切れ対策)。
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    ))
    return (resp.text or "").strip()


def _mock(tag: str, prompt: str) -> str:
    head = prompt.strip().splitlines()[0][:60] if prompt.strip() else ""
    return (f"〔{tag} mock〕APIキー未設定のためダミー出力です。\n"
            f"入力先頭: {head}\n"
            "（本番では実際の文章がここに生成されます）")
