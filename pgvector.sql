create database ragdb;
create user ragu with encrypted password 'yourpassword';
grant all privileges on database ragdb to ragu;

\c ragdb
CREATE EXTENSION if not exists vector;
CREATE TABLE t_documents (id bigserial PRIMARY KEY, doc_name varchar(256), created_at timestamp default now());
						
CREATE TABLE t_document_chunks (id bigserial PRIMARY KEY,
							  doc_id bigserial not null references t_documents(id),
							  chunk jsonb,							
							  embedding vector(384),
							  created_at timestamp default now());

CREATE INDEX ON t_document_chunks USING hnsw (embedding vector_ip_ops) WITH (m = 16, ef_construction = 128);
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA PUBLIC to ragu;
GRANT ALL ON ALL SEQUENCES IN SCHEMA PUBLIC to ragu;
\q

