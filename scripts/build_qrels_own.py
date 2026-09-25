"""自作の設問を qrels 形式に変換する。"""

import json
from pathlib import Path

qrels: dict[str, dict[str, int]] = {}
meta: dict[str, dict] = {}

for i, line in enumerate(Path("eval/dataset_v1.jsonl").open(encoding="utf-8")):
    r = json.loads(line)
    qid = f"own_{i:04d}"

    if r["qtype"] == "unanswerable" or not r.get("gold_chunk_id"):
        qrels[qid] = {}  # 正解なし = 何も返さないのが正解
    else:
        qrels[qid] = {r["gold_chunk_id"]: 1}

    meta[qid] = {
        "question": r["question"],
        "answer": r.get("answer", ""),
        "qtype": r["qtype"],
        "verified": r.get("verified", False),
    }

Path("eval/qrels_own.json").write_text(
    json.dumps(qrels, ensure_ascii=False, indent=2), encoding="utf-8"
)
Path("eval/meta_own.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
)

n_ans = sum(1 for v in qrels.values() if v)
print(f"合計 {len(qrels)} 問（うち正解ありが {n_ans} 問）")
