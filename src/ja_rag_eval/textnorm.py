"""日本語テキストの正規化（归一化）。

入库时和检索时必须调用同一个函数。
片方だけ正規化すると、エラーは出ないまま精度が落ちる。
"""

import re
import unicodedata


def normalize(text: str) -> str:
    """NFKC 正規化と余分な空白の圧縮。"""
    # NFKC：全角英数 → 半角、半角カナ → 全角 など
    text = unicodedata.normalize("NFKC", text)
    # 連続する空白・改行を 1 個にまとめる
    text = re.sub(r"\s+", " ", text)
    return text.strip()
