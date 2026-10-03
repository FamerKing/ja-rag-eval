"""JQaRA の passage を DB に投入する（v2：按 split 装入）。

使い方：
  uv run python scripts/ingest.py dev
  uv run python scripts/ingest.py test
"""

import sys

import psycopg
from datasets import load_dataset

from ja_rag_eval.config import JQARA, PG_DSN, pick_qids

SOURCE = "jqara (wikipedia-utils c400-jawiki-20230403)"
LICENSE = "Wikipedia 由来: CC BY-SA 4.0 / GFDL ・ 設問: JAQKET CC BY-SA 4.0"


def main(split: str) -> None:
    ds = load_dataset(JQARA, split=split)

    # 1. 用哪些题，交给 config.py 决定（这里不再写数字）
    keep = set(pick_qids(split, ds["q_id"]))
    sub = ds.filter(lambda r: r["q_id"] in keep)
    print(f"[{split}] 対象: {len(keep)} 問 / {len(sub)} 行")

    # 2. 同一个 passage 可能是多道题的候选 → 按 passage_row_id 去重
    passages: dict[str, tuple[str, str]] = {}      # chunk_id -> (title, text)
    for pid, title, text in zip(sub["passage_row_id"], sub["title"], sub["text"]):
        passages.setdefault(str(pid), (title, text))
    titles = sorted({t for t, _ in passages.values()})
    print(f"ユニークな passage: {len(passages)} 件 / 記事: {len(titles)} 件")

    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO documents (doc_id, title, source, license, url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO NOTHING
                """,
                [(t, t, SOURCE, LICENSE, f"https://ja.wikipedia.org/wiki/{t}")
                 for t in titles],
            )
            cur.executemany(
                """
                INSERT INTO chunks (chunk_id, doc_id, ord, content, n_chars, split)
                VALUES (%s, %s, NULL, %s, %s, %s)
                ON CONFLICT (chunk_id) DO UPDATE
                  SET content = EXCLUDED.content, split = EXCLUDED.split
                """,
                [(cid, title, text, len(text), split)
                 for cid, (title, text) in passages.items()],
            )
        conn.commit()

    print(f"[{split}] chunks {len(passages)} 件を投入しました")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "test")
