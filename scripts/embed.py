"""チャンクをベクトル化して DB に書き戻す（向量化并写回数据库）。"""

import os

import psycopg
import torch
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
DSN = os.environ["PG_DSN"]

MODEL_NAME = "cl-nagoya/ruri-v3-310m"  # 768 次元 / Apache-2.0 / 商用可
BATCH = 32  # 8GB メモリの Mac なら 8~16 に下げる

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"device: {device}")
model = SentenceTransformer(MODEL_NAME, device=device)


def main() -> None:
    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            # まだベクトル化していないものだけ取る -> 途中で止めても再開できる
            cur.execute("SELECT chunk_id, content FROM chunks WHERE embedding IS NULL")
            rows = cur.fetchall()

        print(f"{len(rows)} 件をベクトル化します")
        for i in range(0, len(rows), BATCH):
            batch = rows[i : i + BATCH]
            vecs = model.encode(
                # ★ 文書側の prefix。忘れると精度が落ちる（エラーは出ない）
                ["検索文書: " + content for _, content in batch],
                normalize_embeddings=True,  # 長さを 1 に揃える（下の説明を参照）
                batch_size=BATCH,
            )
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE chunks SET embedding = %s::vector WHERE chunk_id = %s",
                    [(v.tolist(), cid) for (cid, _), v in zip(batch, vecs)],
                )
            conn.commit()  # バッチごとにコミット（中断に強い）
            print(f"  {min(i + BATCH, len(rows))}/{len(rows)}")


if __name__ == "__main__":
    main()
