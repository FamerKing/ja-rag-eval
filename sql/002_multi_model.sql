-- 002: 多模型对应（複数モデル対応）のマイグレーション
-- 目标：① 给 chunks 加上 split 列  ② 向量从 chunks 搬到「每个模型一张表」
-- 整个文件放在一个事务里：要么全部成功，要么什么都没发生
BEGIN;

-- 记录「这个数据库已经执行过哪些迁移」的表（第一次执行时创建）
CREATE TABLE IF NOT EXISTS schema_migrations (
  version    text PRIMARY KEY,
  applied_at timestamptz DEFAULT now()
);

-- ① chunks 加 split 列。W1 装进来的全部来自 dev
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS split text;
UPDATE chunks SET split = 'dev' WHERE split IS NULL;
ALTER TABLE chunks ALTER COLUMN split SET NOT NULL;

-- ② ruri-v3-310m 专用的向量表。以后每加一个模型，就由 embed.py 自动建一张 emb_xxx
CREATE TABLE IF NOT EXISTS emb_ruri310 (
  chunk_id  text PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  split     text NOT NULL,          -- 和 chunks.split 相同（冗余存一份，检索时不用 JOIN）
  embedding vector(768) NOT NULL
);

-- 把 W1 已经算好的 1.5 万条向量搬过去，省掉重新计算的时间。
-- 旧列还在的时候才搬（这样这个文件执行第二次也不会报错）
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name = 'chunks' AND column_name = 'embedding') THEN
    INSERT INTO emb_ruri310 (chunk_id, split, embedding)
    SELECT chunk_id, split, embedding FROM chunks WHERE embedding IS NOT NULL
    ON CONFLICT (chunk_id) DO NOTHING;
    -- 搬完再删旧列。它上面的 HNSW 索引（chunks_embedding_idx）会一起被删掉
    ALTER TABLE chunks DROP COLUMN embedding;
  END IF;
END $$;

INSERT INTO schema_migrations (version) VALUES ('002') ON CONFLICT DO NOTHING;

COMMIT;
