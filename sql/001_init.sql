-- 启用两个扩展。IF NOT EXISTS 表示已存在就跳过，脚本可以重复执行。
CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector：向量类型和向量检索
CREATE EXTENSION IF NOT EXISTS pgroonga;    -- PGroonga：日语全文检索

-- 文档表：一份 PDF / 一个法令 = 一行
CREATE TABLE documents (
  doc_id      text PRIMARY KEY,   -- 文档的唯一编号，我们用文件名
  title       text NOT NULL,      -- 标题
  source      text NOT NULL,      -- 来源（白書 / 法令 など）
  license     text NOT NULL,      -- 许可证与出处。从第一天就记录，这个习惯在金融/公共案件里会救你
  path        text NOT NULL,      -- 本地文件路径
  ingested_at timestamptz DEFAULT now()   -- 入库时间，带时区
);

-- 文本块表：把文档切碎之后的每一小段 = 一行。检索的基本单位就是它。
CREATE TABLE chunks (
  chunk_id  text PRIMARY KEY,     -- 形如 "文件名#0007"，Day 4 的正解标签就用这个
  doc_id    text NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
                                  -- 外键：删除文档时，它的所有文本块自动删除
  page_no   int,                  -- 页码（有就填，没有留空）
  ord       int NOT NULL,         -- 在文档内的第几块，用来恢复顺序
  content   text NOT NULL,        -- 正文
  n_chars   int NOT NULL,         -- 字符数，用来做统计和排查
  embedding vector(768)           -- 向量。768 是 ruri-v3-310m 这个模型的输出维度
);

-- 日语关键词检索用的索引。默认用 N-gram 分词，够用。
-- （想改成 MeCab 形态素解析要加 WITH (tokenizer = 'TokenMecab')，W3 再讲。）
CREATE INDEX pgroonga_chunks_content ON chunks USING pgroonga (content);

-- 注意：向量索引现在不建。空表上建索引没有意义，Day 5 数据进去之后再建。