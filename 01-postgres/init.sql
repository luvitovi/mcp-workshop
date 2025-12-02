-- Script de inicialización de PostgreSQL con pgvector
-- Ejecutar como superusuario de PostgreSQL

-- Crear extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear tabla para almacenar documentos vectorizados
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(384),  -- Dimensión para all-MiniLM-L6-v2
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Crear índice para búsqueda vectorial eficiente
-- Usando HNSW (Hierarchical Navigable Small World) para mejor rendimiento
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks 
USING hnsw (embedding vector_cosine_ops);

-- Crear índice para búsquedas por nombre de documento
CREATE INDEX IF NOT EXISTS document_chunks_name_idx 
ON document_chunks(document_name);

-- Crear función para búsqueda por similitud
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector(384),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id INTEGER,
    document_name VARCHAR(255),
    chunk_text TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        document_chunks.id,
        document_chunks.document_name,
        document_chunks.chunk_text,
        1 - (document_chunks.embedding <=> query_embedding) as similarity
    FROM document_chunks
    WHERE 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Crear usuario para la aplicación (opcional)
-- CREATE USER rag_user WITH PASSWORD 'tu_password_seguro';
-- GRANT ALL PRIVILEGES ON DATABASE rag_documents TO rag_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rag_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rag_user;