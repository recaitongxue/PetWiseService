-- 建表之外的知识库 DDL：postgres-only，多条语句用 ;; 分隔

-- 1. 向量索引：HNSW 在召回速度与构建成本之间最均衡
CREATE INDEX IF NOT EXISTS ix_kb_chunk_embedding_hnsw
    ON kb_chunk USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);;

-- 2. 关键词通道：pg_trgm 支持 ILIKE 走索引，
--    中文不走 to_tsvector 分词，因此这里只服务于英文/数字/药品名的模糊匹配
CREATE EXTENSION IF NOT EXISTS pg_trgm;;

CREATE INDEX IF NOT EXISTS ix_kb_chunk_content_trgm
    ON kb_chunk USING gin (content gin_trgm_ops);;

-- 3. 元信息组合索引：按物种 + 来源类型过滤是最高频的查询形态
CREATE INDEX IF NOT EXISTS ix_kb_document_filter
    ON kb_document (source_type, species);;
