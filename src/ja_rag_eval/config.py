"""プロジェクト共通の設定（全项目共用的配置）。

W1 里 N_QUESTIONS 写在两个脚本里，必须手动保持一致。
W2 把它们集中到这里：所有脚本都从这个文件读取，只改一处。
"""

import os
import random

from dotenv import load_dotenv

load_dotenv()

PG_DSN = os.environ.get(
    "PG_DSN", "postgresql://postgres:postgres@localhost:5432/ragdb"
)

JQARA = "hotchpotch/JQaRA"

# 每个 split 用多少道题。None = 全部
SPLITS: dict[str, int | None] = {
    "dev": 300,    # W1 と同じ。ruri 系は学習に使っているので「参考値」扱い
    "test": 500,   # W2 からの主評価（全 1,667 問のうち 500 問）
}

SEED = 42          # 抽样用的随机种子。固定它，每次抽到的题目都一样


def pick_qids(split: str, all_qids) -> list[str]:
    """决定这个 split 用哪些题。ingest.py 和 build_qrels.py 都调用它。"""
    qids = sorted(set(all_qids))
    n = SPLITS[split]
    if n is None or n >= len(qids):
        return qids
    if split == "dev":
        return qids[:n]                 # W1 と同じ選び方（互換性のため）
    # test は「先頭 N 問」だと出典が偏るので、固定シードで無作為抽出
    return sorted(random.Random(SEED).sample(qids, n))
