from ja_rag_eval.textnorm import normalize


def test_zenkaku_eisuu():
    assert normalize("ＡＩ　2026年") == "AI 2026年"


def test_hankaku_kana():
    assert normalize("ｱｲｳ") == "アイウ"


def test_whitespace():
    assert normalize("  改行\nと   空白  ") == "改行 と 空白"
