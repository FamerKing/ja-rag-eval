from datasets import load_dataset


def main() -> None:
    # 第一次运行会下载（几百 MB），之后读本地缓存
    ds = load_dataset("hotchpotch/JQaRA", split="dev")

    print("=" * 60)
    print("列名 :", ds.column_names)
    print("行数 :", len(ds))
    print("質問数:", len(set(ds["q_id"])))
    print()

    # 1 行目の中身を全部見る
    print("--- 1 行目 ---")
    for key, value in ds[0].items():
        print(f"  {key:16} = {str(value)[:70]}")
    print()

    # 同じ質問の候補をまとめて見る（正解がどれかを目で確認する）
    target_q = ds[0]["q_id"]
    rows = [r for r in ds.select(range(300)) if r["q_id"] == target_q]

    print(f"--- 質問 {target_q} の候補 {len(rows)} 件 ---")
    print(f"質問: {rows[0]['question']}")
    print(f"答え: {rows[0]['answers']}")
    print()
    for r in rows[:12]:  # 长了刷屏，先看前 12 条
        mark = "★ 正解" if r["label"] == 1 else "      "
        print(f"{mark} [{r['passage_row_id']}] {r['title']}")
        print(f"        {r['text'][:60]}...")

    n_gold = sum(1 for r in rows if r["label"] == 1)
    print()
    print(f"この質問の正解 passage は {n_gold} 件でした")


if __name__ == "__main__":
    main()
