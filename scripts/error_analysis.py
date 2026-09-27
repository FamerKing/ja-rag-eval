"""検索に失敗した設問を見る（看失败案例）。

失敗の定義：その設問の正解が 1 つも top-K に入らなかったこと。
"""

import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from ja_rag_eval.retrieve import DenseRetriever

load_dotenv()

EVAL_SET = "jqara"  # "jqara" か "own"。見たい評価セットを選ぶ
K = 5
SHOW = 5  # 表示する失敗の件数

qrels = json.loads(Path(f"eval/qrels_{EVAL_SET}.json").read_text(encoding="utf-8"))
meta = json.loads(Path(f"eval/meta_{EVAL_SET}.json").read_text(encoding="utf-8"))
retriever = DenseRetriever()


def preview(cur, chunk_id: str, n: int = 120) -> str:
    """chunk の先頭 n 文字を返す。"""
    cur.execute(
        "SELECT left(content, %s) FROM chunks WHERE chunk_id = %s", (n, chunk_id)
    )
    row = cur.fetchone()
    return row[0] if row else "(DB に見つかりません)"


answerable = {q: g for q, g in qrels.items() if g}
failures = []
for qid, gold in answerable.items():
    hits = list(retriever.search(meta[qid]["question"], k=K))
    if not set(gold) & set(hits):  # 正解が 1 つも top-K に入らなかった
        failures.append((qid, list(gold), hits))

print(
    f"[{EVAL_SET}] 失敗 {len(failures)} / {len(answerable)} 問"
    f"（正解が 1 つも top-{K} に入らなかった設問）\n"
)

with psycopg.connect(os.environ["PG_DSN"]) as conn, conn.cursor() as cur:
    for qid, gold_ids, hits in failures[:SHOW]:
        print("=" * 70)
        qtype = meta[qid].get("qtype", "-")  # JQaRA の meta には qtype がない
        print(f"[{qtype}] {meta[qid]['question']}")
        print(f"\n正解であるべき（{len(gold_ids)} 件のうち 1 件）: {gold_ids[0]}")
        print(f"  {preview(cur, gold_ids[0])}")
        if hits:
            print(f"\n実際の 1 位: {hits[0]}")
            print(f"  {preview(cur, hits[0])}")
        print()
