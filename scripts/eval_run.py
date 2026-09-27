"""検索性能を測定して results/ に記録する（判卷并记录）。

再现性の 3 つの規律:
1. 設定は全部 dict に入れ、その JSON のハッシュを run_id にする
2. 結果は 1 実験 1 ファイル。上書きしない
3. qrels は絶対に触らない（点数が悪いからといって尺を変えない）
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from ranx import Qrels, Run, evaluate

from ja_rag_eval.retrieve import DenseRetriever

# ---- 今回の実験設定。ここを変えたら run_id も自動で変わる ----
CONFIG = {
    "corpus": "jqara-dev-300q-candidates",  # 300 問の候補の和集合
    "chunking": "c400 (upstream)",
    "embedding": "cl-nagoya/ruri-v3-310m",
    "retrieval": "dense-cosine",
    "top_k": 20,
    "keyword": None,  # W3 で PGroonga を足す
    "rerank": None,  # W4 で足す
}
RUN_ID = hashlib.sha1(json.dumps(CONFIG, sort_keys=True).encode()).hexdigest()[:10]

METRICS = ["recall@5", "recall@20", "ndcg@10", "mrr@10", "precision@3"]

# 評価セット：(タグ, qrels のパス, meta のパス)
EVAL_SETS = [
    ("jqara", "eval/qrels_jqara.json", "eval/meta_jqara.json"),
    ("own_v1", "eval/qrels_own.json", "eval/meta_own.json"),
]


def run_eval(qrels_path: str, meta_path: str, tag: str, retriever) -> dict:
    qrels_raw = json.loads(Path(qrels_path).read_text(encoding="utf-8"))
    meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))

    # 正解のない設問（unanswerable）は検索指標では測れないので除外
    qrels_raw = {q: d for q, d in qrels_raw.items() if d}

    run_dict = {}
    for n, qid in enumerate(qrels_raw, 1):
        run_dict[qid] = retriever.search(meta[qid]["question"], k=CONFIG["top_k"])
        if n % 50 == 0:
            print(f"  {tag}: {n}/{len(qrels_raw)}")

    scores = evaluate(Qrels(qrels_raw), Run(run_dict, name=RUN_ID), METRICS)
    return {"tag": tag, "n_queries": len(qrels_raw), "scores": scores}


def main() -> None:
    retriever = DenseRetriever(CONFIG["embedding"])

    results = []
    for tag, qrels_path, meta_path in EVAL_SETS:
        if not Path(qrels_path).exists():  # 合成をスキップした人向け
            print(f"skip: {qrels_path} がありません")
            continue
        results.append(run_eval(qrels_path, meta_path, tag, retriever))

    Path("results").mkdir(exist_ok=True)
    record = {
        "run_id": RUN_ID,
        "at": datetime.now(UTC).isoformat(),
        "config": CONFIG,
        "results": results,
    }
    Path(f"results/{RUN_ID}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n=== run_id: {RUN_ID} ===")
    for r in results:
        print(f"[{r['tag']}] n={r['n_queries']}")
        for k, v in r["scores"].items():
            print(f"  {k:<14} {v:.4f}")


if __name__ == "__main__":
    main()
