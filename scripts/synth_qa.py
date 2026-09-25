"""チャンクから評価用の設問を合成する（合成 QA）。

最重要的一点：必须记录每个问题是从哪个 chunk 生成的。
那个 chunk_id 就是这道题的标准答案。没有它，评测集是废的。
"""

import json
import os
import random
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI  # Gemini / Anthropic 用的话换成对应 SDK

load_dotenv()
DSN = os.environ["PG_DSN"]
client = OpenAI()  # 自动读取环境变量 OPENAI_API_KEY

# 生成模型用中等档位就够，不需要最贵的
GEN_MODEL = "gpt-5.6-terra"

PROMPT = """あなたは日本語の業務文書から検索評価用の設問を作る専門家です。
以下の文書断片だけを根拠に、指定されたタイプの質問を1問作ってください。

制約:
- 質問文の中に答えを含めないこと
- この断片を読まなければ答えられない質問にすること（一般常識で答えられる質問は不可）
- 固有名詞・数値・日付はそのまま正確に使うこと
- 「この表によると」のような、断片への参照表現は使わないこと

タイプ: {qtype}

文書断片:
---
{chunk}
---

JSON で出力してください: {{"question": "...", "answer": "...", "qtype": "{qtype}"}}"""

# STEP 2 で決めた分布に合わせる（合計 10、これを 6 回まわして 60 問）
TYPE_POOL = (
    ["fact"] * 3
    + ["entity_number"] * 2
    + ["table"] * 2
    + ["conditional"] * 2
    + ["multi_hop"] * 1
)


def sample_chunks(n: int) -> list[tuple[str, str]]:
    """ある程度の長さがあるチャンクをランダムに n 件取ってくる。"""
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_id, content FROM chunks
            WHERE n_chars > 250
            ORDER BY random() LIMIT %s
            """,
            (n,),
        )
        return cur.fetchall()


def main() -> None:
    rows = []
    chunks = sample_chunks(60)
    print(f"{len(chunks)} 件のチャンクから設問を生成します")

    for i, (chunk_id, content) in enumerate(chunks, 1):
        qtype = random.choice(TYPE_POOL)
        try:
            resp = client.chat.completions.create(
                model=GEN_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": PROMPT.format(qtype=qtype, chunk=content),
                    }
                ],
                response_format={"type": "json_object"},  # JSON で返すよう強制
            )
            item = json.loads(resp.choices[0].message.content)
        except Exception as e:  # 1 件失敗しても全体を止めない
            print(f"  [{i}] 失敗: {e}")
            continue

        item["gold_chunk_id"] = chunk_id  # ← これが正解ラベル。絶対に落とさない
        item["verified"] = False  # 人手確認済みフラグ。STEP 6 で立てる
        rows.append(item)
        print(f"  [{i}/{len(chunks)}] {qtype}: {item['question'][:40]}...")

    out = Path("eval")
    out.mkdir(exist_ok=True)
    with (out / "dataset_raw.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} 問を eval/dataset_raw.jsonl に書き出しました")


if __name__ == "__main__":
    main()
