-- 启用两个扩展。IF NOT EXISTS 表示已存在就跳过，脚本可以重复执行。
CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector：向量类型和向量检索
CREATE EXTENSION IF NOT EXISTS pgroonga;    -- PGroonga：日语全文检索

-- 文档表：一篇 Wikipedia 记事 = 一行
CREATE TABLE documents (
  doc_id      text PRIMARY KEY,   -- 记事的唯一编号。这次用记事标题
  title       text NOT NULL,      -- 标题
  source      text NOT NULL,      -- 来源（jawiki など）
  license     text NOT NULL,      -- 许可证与出处。从第一天就记录，这个习惯在金融/公共案件里会救你
  url         text,               -- 原文链接，出典附与时要用
  ingested_at timestamptz DEFAULT now()   -- 入库时间，带时区
);

-- 文本块表：检索的基本单位。一段 passage = 一行。
CREATE TABLE chunks (
  chunk_id  text PRIMARY KEY,     -- 段落的唯一编号。Day 4 的正解标签就用这个
  doc_id    text NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
                                  -- 外键：删除记事时，它的所有文本块自动删除
  ord       int,                  -- 在记事内的第几段，用来恢复顺序
  content   text NOT NULL,        -- 正文
  n_chars   int NOT NULL,         -- 字符数，用来做统计和排查
  embedding vector(768)           -- 向量。768 是 ruri-v3-310m 这个模型的输出维度
);

-- 日语关键词检索用的索引。默认用 N-gram 分词，够用。
-- （想改成 MeCab 形态素解析要加 WITH (tokenizer = 'TokenMecab')，W3 再讲。）
CREATE INDEX pgroonga_chunks_content ON chunks USING pgroonga (content);

-- 注意：向量索引现在不建。空表上建索引没有意义，Day 5 数据进去之后再建。