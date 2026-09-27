# ja-rag-eval — 日本語 RAG の検索精度を測り、改善する

「実装より先に評価をつくる」という方針で、日本語文書に対する
RAG の検索性能を毎週改善していく記録です。

## なぜ評価を先に作ったか

番号のない改善は再現できず、説明もできない。
だから最初の週に、実装ではなく評価セットを作りました。

## 評価セット

- 公開ベンチマーク：JQaRA dev の先頭 300 問（`hotchpotch/JQaRA`）
- 自作の合成設問：約 50 問（LLM 生成 → answer-in-context フィルタ → 人手検証）
  - タイプ別に設計：事実 / 固有名詞・数値 / 表 / 条件 / 複数箇所統合 / **答えられない**
  - フィルタの除外率：XX%

## 評価の設定

- 検索対象：300 問の候補 passage の和集合（約 1.5 万件）から検索する
- JQaRA 公式の設定（test split・各設問の候補 100 件の中で並べ替える）とは異なるため、
  公開スコアとは直接比較できない

## 改善の記録

| Week | 構成 | Recall@5 | nDCG@10 | MRR@10 |
|---|---|---|---|---|
| W1 | c400 passages + ruri-v3-310m dense | 0.54 | 0.48 | 0.45 |
| W2 | + embedding 選型 + タイトル付与 | — | — | — |
| W3 | + PGroonga ハイブリッド検索（RRF） | — | — | — |
| W4 | + リランカー + 分割の実験 | — | — | — |

## 再現方法

```bash
docker compose up -d
uv sync
uv run pytest
uv run python scripts/ingest.py
uv run python scripts/build_qrels.py
uv run python scripts/embed.py
uv run python scripts/eval_run.py
```

## 出典・ライセンス

- コーパス：日本語 Wikipedia 由来（CC BY-SA 4.0 / GFDL）
- 評価データ：hotchpotch/JQaRA（設問は JAQKET CC BY-SA 4.0）
- モデル：cl-nagoya/ruri-v3-310m（Apache-2.0）