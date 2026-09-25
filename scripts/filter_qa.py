"""一般知識だけで答えられる設問を除外する（answer-in-context フィルタ）。"""

import json
from pathlib import Path

from anthropic import Anthropic  # 生成に OpenAI を使ったので、判定は別系統で
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

CHECK = """次の質問に、あなたの一般知識だけで正確に答えられますか。
特定の文書を参照しないと答えられない場合は NO と答えてください。

質問: {q}

YES か NO の一語のみで答えてください。"""

src = Path("eval/dataset_raw.jsonl")
rows = [json.loads(line) for line in src.open(encoding="utf-8")]

kept = []
for i, r in enumerate(rows, 1):
    msg = client.messages.create(
        model="claude-haiku-4-5",  # 判定は安価なモデルで十分
        max_tokens=8,
        messages=[{"role": "user", "content": CHECK.format(q=r["question"])}],
    )
    verdict = msg.content[0].text.strip().upper()
    if verdict.startswith("NO"):  # 文書がないと答えられない = 良い設問
        kept.append(r)
    else:
        print(f"  除外 [{i}]: {r['question'][:40]}...")

out = Path("eval/dataset_v1.jsonl")
with out.open("w", encoding="utf-8") as f:
    for r in kept:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

rate = (len(rows) - len(kept)) / len(rows) * 100
print(f"{len(rows)} 問 -> {len(kept)} 問（除外率 {rate:.1f}%）")
