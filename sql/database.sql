-- 1. Habilitar la extensión de vectores (Obligatorio)
CREATE
    EXTENSION IF NOT EXISTS vector;
CREATE
    EXTENSION IF NOT EXISTS "uuid-ossp";
-- Para generar UUIDs

-- 2. Tabla de Servicios (Lo que llena tu Dropdown en Electron)
CREATE TABLE services
(
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE, -- Ej: 'SAP', 'VPN', 'Impresoras'
    description TEXT,
    status      BOOLEAN DEFAULT TRUE
);

-- TYPE STATUS
CREATE TYPE document_status AS ENUM ('PENDING', 'PROCESSING', 'READY', 'ERROR');

-- 3. Tabla de Documentos (Tu registro administrativo y enlace a S3)
CREATE TABLE documents
(
    id          UUID PRIMARY KEY         DEFAULT uuid_generate_v4(),
    service_id  INT REFERENCES services (id) ON DELETE CASCADE,
    title       VARCHAR(255) NOT NULL,
    s3_key      VARCHAR(512) NOT NULL,                    -- Ruta en AWS S3 bucket
    hash_md5    VARCHAR(32),                              -- Para evitar subir el mismo PDF dos veces
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status      document_status          DEFAULT 'PENDING'-- 'PENDIENTE', 'PROCESANDO', 'LISTO', 'ERROR'
);

CREATE TABLE document_chunks
(
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents (id) ON DELETE CASCADE,

    -- El fragmento de texto real
    content     TEXT NOT NULL,

    -- Metadatos para la fuente de información
    page_number INT,

    -- El vector generado por el modelo de Google
    embedding   VECTOR(768)
);

-- 5. Índices para velocidad (HNSW es mucho más rápido que IVFFlat)
-- Esto hace que la búsqueda sea milisegundos incluso con millones de filas.
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Índice para que el filtrado por documento sea rápido al borrar
CREATE INDEX ON document_chunks (document_id);


-- users
CREATE TABLE users
(
    id            UUID PRIMARY KEY         DEFAULT uuid_generate_v4(),
    full_name     VARCHAR(255) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at    TIMESTAMP WITH TIME ZONE
);


