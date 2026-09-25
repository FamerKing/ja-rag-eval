"""JQaRA の passage をデータベースに投入する（把段落装进数据库）。

今天只装「被检索的段落」。
问题和正解是 Day 4 的事，会存成 eval/ 下的 JSON 文件。

设计要点：幂等（idempotent / 冪等）——
同一个脚本跑两次，结果和跑一次一样，不会产生重复数据。
"""

import os

import psycopg
from datasets import load_dataset
from dotenv import load_dotenv

load_dotenv()  # .env から PG_DSN を読む
DSN = os.environ.get("PG_DSN", "postgresql://postgres:postgres@localhost:5432/ragdb")

# W1 は軽く始める。300 問ぶんの候補だけを入れる。
# None にすると dev 全件（1,737 問）。W2 で増やす。
N_QUESTIONS = 300

SOURCE = "jqara-dev (wikipedia-utils c400-jawiki-20230403)"
LICENSE = "Wikipedia 由来: CC BY-SA 4.0 / GFDL ・ 設問: JAQKET CC BY-SA 4.0"


def main() -> None:
    ds = load_dataset("hotchpotch/JQaRA", split="dev")

    # 1. 対象の質問を決める（件数を絞ってから中身を触ると速い）
    all_qids = sorted(set(ds["q_id"]))
    keep = set(all_qids if N_QUESTIONS is None else all_qids[:N_QUESTIONS])
    sub = ds.filter(lambda r: r["q_id"] in keep)
    print(f"対象: {len(keep)} 問 / {len(sub)} 行")

    # 2. 同じ passage が複数の質問の候補に出てくるので、重複を除く
    #    キーは passage_row_id。これがそのまま chunk_id になる。
    passages: dict[str, tuple[str, str]] = {}  # chunk_id -> (title, text)
    for pid, title, text in zip(sub["passage_row_id"], sub["title"], sub["text"]):
        passages.setdefault(str(pid), (title, text))
    print(f"ユニークな passage: {len(passages)} 件")

    # 3. 記事（documents）は title 単位でまとめる
    titles = sorted({title for title, _ in passages.values()})

    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO documents (doc_id, title, source, license, url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO UPDATE
                  SET source = EXCLUDED.source, license = EXCLUDED.license
                """,
                [
                    (t, t, SOURCE, LICENSE, f"https://ja.wikipedia.org/wiki/{t}")
                    for t in titles
                ],
            )
            cur.executemany(
                """
                INSERT INTO chunks (chunk_id, doc_id, ord, content, n_chars)
                VALUES (%s, %s, NULL, %s, %s)
                ON CONFLICT (chunk_id) DO UPDATE
                  SET content = EXCLUDED.content
                """,
                [
                    (cid, title, text, len(text))
                    for cid, (title, text) in passages.items()
                ],
            )
        conn.commit()  # 全部成功してから確定させる

    print(f"documents {len(titles)} 件 / chunks {len(passages)} 件を投入しました")


if __name__ == "__main__":
    main()
