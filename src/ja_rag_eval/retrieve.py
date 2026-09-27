"""ベクトル検索（向量检索）。

W1 的 baseline 故意保持最简单：单一 embedding、cosine、top-k。
W3 会在这里加上 PGroonga 的关键词检索并做融合，
W4 会加上重排。所以这个类的接口要稳定。
"""

import os

import psycopg
import torch
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
DSN = os.environ["PG_DSN"]


class DenseRetriever:
    def __init__(self, model_name: str = "cl-nagoya/ruri-v3-310m") -> None:
        self.model_name = model_name
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=device)

    def search(self, query: str, k: int = 20) -> dict[str, float]:
        """質問 -> {chunk_id: 類似度} を上位 k 件返す。"""
        vec = self.model.encode(
            # ★ クエリ側の prefix。文書側の「検索文書: 」と対になる
            ["検索クエリ: " + query],
            normalize_embeddings=True,
        )[0].tolist()

        with psycopg.connect(DSN) as conn, conn.cursor() as cur:
            # ef_search を上げると精度が上がり速度が落ちる（既定 40）
            cur.execute("SET LOCAL hnsw.ef_search = 100")
            cur.execute(
                """
                SELECT chunk_id, 1 - (embedding <=> %s::vector) AS score
                FROM chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vec, vec, k),
            )
            return {chunk_id: float(score) for chunk_id, score in cur.fetchall()}
