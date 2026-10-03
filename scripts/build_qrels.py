"""JQaRA から qrels・meta・候補リストを作る（v2：按 split 生成）。

使い方：
  uv run python scripts/build_qrels.py dev
  uv run python scripts/build_qrels.py test

产出（以 test 为例）：
  eval/qrels_jqara_test.json   问题ID -> {正解 passage ID: 1}
  eval/meta_jqara_test.json    问题ID -> 问题文本・答案
  eval/cand_jqara_test.json    问题ID -> [这道题的全部候选 passage ID]  ← W2 新增
"""

import json
import sys
from pathlib import Path

from datasets import load_dataset

from ja_rag_eval.config import JQARA, pick_qids


def main(split: str) -> None:
    ds = load_dataset(JQARA, split=split)
    keep = set(pick_qids(split, ds["q_id"]))

    qrels: dict[str, dict[str, int]] = {}
    meta: dict[str, dict] = {}
    cand: dict[str, list[str]] = {}

    for q_id, question, answers, pid, label in zip(
        ds["q_id"], ds["question"], ds["answers"],
        ds["passage_row_id"], ds["label"],
    ):
        if q_id not in keep:
            continue
        qid = f"jqara_{q_id}"
        qrels.setdefault(qid, {})
        cand.setdefault(qid, []).append(str(pid))   # 正解も不正解も全部
        if label == 1:
            qrels[qid][str(pid)] = 1
        meta.setdefault(qid, {"question": question, "answers": answers,
                              "source": f"{JQARA} ({split})"})

    out = Path("eval")
    out.mkdir(exist_ok=True)
    for name, obj in [("qrels", qrels), ("meta", meta), ("cand", cand)]:
        (out / f"{name}_jqara_{split}.json").write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    n_gold = [len(v) for v in qrels.values() if v]
    n_cand = [len(v) for v in cand.values()]
    print(f"[{split}] {len(qrels)} 問（うち正解ありが {len(n_gold)} 問）")
    print(f"  1 問あたり: 候補 {sum(n_cand) / len(n_cand):.0f} 件 / "
          f"正解 平均 {sum(n_gold) / len(n_gold):.1f} 件（最大 {max(n_gold)} 件）")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "test")
