"""JQaRA から qrels を作る（生成标准答案表）。

Day 3 の ingest.py と同じ N_QUESTIONS を使うこと。
ここがずれると「正解がそもそも DB に入っていない」状態になる。
"""

import json
from pathlib import Path

from datasets import load_dataset

N_QUESTIONS = 300  # ← ingest.py と必ず揃える

OUT = Path("eval")
OUT.mkdir(exist_ok=True)

ds = load_dataset("hotchpotch/JQaRA", split="dev")
all_qids = sorted(set(ds["q_id"]))
keep = set(all_qids[:N_QUESTIONS])

qrels: dict[str, dict[str, int]] = {}  # 问题ID -> {正解块ID: 相关度}
meta: dict[str, dict] = {}  # 问题ID -> 问题文本などの付帯情報

for q_id, question, answers, pid, label in zip(
    ds["q_id"],
    ds["question"],
    ds["answers"],
    ds["passage_row_id"],
    ds["label"],
):
    if q_id not in keep:
        continue
    qid = f"jqara_{q_id}"
    qrels.setdefault(qid, {})
    if label == 1:  # ← label が 1 の passage だけが正解
        qrels[qid][str(pid)] = 1
    meta.setdefault(
        qid,
        {
            "question": question,
            "answers": answers,
            "source": "hotchpotch/JQaRA (dev)",
        },
    )

n_with_gold = sum(1 for v in qrels.values() if v)
avg_gold = sum(len(v) for v in qrels.values()) / max(n_with_gold, 1)

(OUT / "qrels_jqara.json").write_text(
    json.dumps(qrels, ensure_ascii=False, indent=2), encoding="utf-8"
)
(OUT / "meta_jqara.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
)

print(f"{len(qrels)} 問（うち正解ありが {n_with_gold} 問）")
print(f"1 問あたりの正解 passage 数: 平均 {avg_gold:.1f} 件")
