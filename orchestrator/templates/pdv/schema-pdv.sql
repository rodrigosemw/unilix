-- ============================================================
-- ComandaFácil — Schema do banco de dados
-- Módulo PDV da plataforma Unilix
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS pdv_usuarios (
  id          TEXT PRIMARY KEY,
  nome        TEXT NOT NULL,
  usuario     TEXT NOT NULL UNIQUE,
  senha       TEXT NOT NULL,
  role        TEXT NOT NULL DEFAULT 'atendente',
  ativo       BOOLEAN NOT NULL DEFAULT true,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO pdv_usuarios (id, nome, usuario, senha, role)
VALUES ('usr_admin', 'Administrador', 'admin', '__ADMIN_HASH__', 'admin')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS pdv_produtos (
  id          TEXT PRIMARY KEY,
  nome        TEXT NOT NULL,
  categoria   TEXT NOT NULL DEFAULT 'Geral',
  preco       NUMERIC(10,2) NOT NULL DEFAULT 0,
  estoque     NUMERIC(10,3) NOT NULL DEFAULT 0,
  estoque_min NUMERIC(10,3) NOT NULL DEFAULT 0,
  custo       NUMERIC(10,2) NOT NULL DEFAULT 0,
  unidade     TEXT NOT NULL DEFAULT 'un',
  foto_url    TEXT,
  ativo       BOOLEAN NOT NULL DEFAULT true,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pdv_clientes (
  id          TEXT PRIMARY KEY,
  nome        TEXT NOT NULL,
  telefone    TEXT,
  obs         TEXT,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pdv_comandas (
  id            TEXT PRIMARY KEY,
  numero        INTEGER,
  cliente_nome  TEXT NOT NULL DEFAULT 'Cliente',
  cliente_id    TEXT REFERENCES pdv_clientes(id) ON DELETE SET NULL,
  status        TEXT NOT NULL DEFAULT 'aberta',
  total         NUMERIC(10,2) NOT NULL DEFAULT 0,
  desconto      NUMERIC(10,2) NOT NULL DEFAULT 0,
  pagamento     TEXT,
  obs           TEXT,
  aberta_por    TEXT,
  fechada_por   TEXT,
  fechada_em    TIMESTAMPTZ,
  aberta_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE SEQUENCE IF NOT EXISTS pdv_comanda_seq START 1;

CREATE TABLE IF NOT EXISTS pdv_itens (
  id          TEXT PRIMARY KEY,
  comanda_id  TEXT NOT NULL REFERENCES pdv_comandas(id) ON DELETE CASCADE,
  produto_id  TEXT NOT NULL REFERENCES pdv_produtos(id) ON DELETE CASCADE,
  nome_prod   TEXT NOT NULL,
  preco_unit  NUMERIC(10,2) NOT NULL,
  quantidade  NUMERIC(10,3) NOT NULL DEFAULT 1,
  para_levar  BOOLEAN NOT NULL DEFAULT false,
  obs         TEXT,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comandas_status    ON pdv_comandas(status);
CREATE INDEX IF NOT EXISTS idx_comandas_aberta_em ON pdv_comandas(aberta_em DESC);
CREATE INDEX IF NOT EXISTS idx_itens_comanda      ON pdv_itens(comanda_id);
CREATE INDEX IF NOT EXISTS idx_itens_produto      ON pdv_itens(produto_id);
CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON pdv_produtos(categoria);
CREATE INDEX IF NOT EXISTS idx_produtos_ativo     ON pdv_produtos(ativo);

-- Roles PostgREST
CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD '__DB_PASS__';
GRANT anon TO authenticator;
GRANT authenticated TO authenticator;

GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;
