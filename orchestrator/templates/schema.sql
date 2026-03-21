-- Roles PostgREST
create role anon nologin;
create role authenticated nologin;
create role authenticator noinherit login password '{{DB_PASS}}';
grant anon to authenticator;
grant authenticated to authenticator;

-- ============================================================
-- CORE — compartilhado entre todos os módulos
-- ============================================================
create table workspaces (
  id uuid primary key default gen_random_uuid(),
  app_name text not null,
  plan text default 'starter',
  monthly_price numeric(10,2) default 0,
  logo_url text, accent_color text,
  status text default 'active',
  modulos text[] default '{estoque}',
  created_at timestamptz default now()
);

create table users (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete cascade,
  login text not null, senha text not null,
  nome text, role text default 'user', avatar text default '👤',
  email text, sends_to text[], last_seen timestamptz,
  reset_requested boolean default false, reset_temp_pass text, reset_at timestamptz,
  modulos_acesso text[] default '{"estoque"}',
  settings jsonb default '{}',
  created_at timestamptz default now(),
  unique(workspace_id, login)
);

-- ============================================================
-- MÓDULO ESTOQUE — ListaFácil
-- ============================================================
create table categories (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete cascade,
  nome text not null, emoji text, cor text, ordem int default 0,
  created_at timestamptz default now()
);

create table items (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete cascade,
  category_id uuid references categories(id) on delete cascade,
  nome text not null, unidade text, fornecedor text,
  quantidade_padrao numeric(10,2) default 1,
  preco_custo numeric(10,2) default 0,
  estoque_atual numeric(10,3) default 0,
  estoque_minimo numeric(10,3) default 0,
  created_at timestamptz default now(),
  unique(workspace_id, nome)
);

create table template_lists (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete cascade,
  titulo text not null, emoji text, color text,
  allowed_users text[], receivers text[], items jsonb default '[]',
  created_at timestamptz default now()
);

create table list_submissions (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete cascade,
  template_id uuid references template_lists(id) on delete cascade,
  titulo text, submitted_by text, sent_to text[], shared_with text[],
  status text default 'enviada', items jsonb default '[]',
  checked_state jsonb default '{}', parent_id uuid, hidden_by text[],
  updated_at timestamptz default now(),
  completed_by text, completed_at timestamptz,
  created_at timestamptz default now()
);

create table notifications (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete cascade,
  to_login text, from_login text, type text,
  payload jsonb, read bool default false,
  ref_id uuid, ref_type text, extra text, message text,
  created_at timestamptz default now()
);

create table checked_items (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete cascade,
  submission_id uuid references list_submissions(id) on delete cascade,
  item_id text not null,
  checked boolean default false,
  checked_by text, checked_name text,
  updated_at timestamptz default now(),
  checked_at timestamptz default now(),
  unique(submission_id, item_id)
);

-- ============================================================
-- MÓDULO PDV — ComandaFácil
-- ============================================================
create table pdv_produtos (
  id text primary key,
  workspace_id uuid references workspaces(id) on delete cascade,
  nome text not null,
  categoria text not null default 'Geral',
  preco numeric(10,2) not null default 0,
  estoque numeric(10,3) not null default 0,
  estoque_min numeric(10,3) not null default 0,
  custo numeric(10,2) not null default 0,
  unidade text not null default 'un',
  foto_url text,
  item_id uuid references items(id) on delete set null,
  ativo boolean not null default true,
  criado_em timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table pdv_clientes (
  id text primary key,
  workspace_id uuid references workspaces(id) on delete cascade,
  nome text not null,
  telefone text, obs text,
  criado_em timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table pdv_comandas (
  id text primary key,
  workspace_id uuid references workspaces(id) on delete cascade,
  numero integer,
  cliente_nome text not null default 'Cliente',
  cliente_id text references pdv_clientes(id) on delete set null,
  status text not null default 'aberta',
  total numeric(10,2) not null default 0,
  desconto numeric(10,2) not null default 0,
  pagamento text, obs text,
  aberta_por text, fechada_por text, fechada_em timestamptz,
  aberta_em timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create sequence pdv_comanda_seq start 1;

create table pdv_itens (
  id text primary key,
  workspace_id uuid references workspaces(id) on delete cascade,
  comanda_id text not null references pdv_comandas(id) on delete cascade,
  produto_id text not null references pdv_produtos(id) on delete cascade,
  nome_prod text not null,
  preco_unit numeric(10,2) not null,
  quantidade numeric(10,3) not null default 1,
  para_levar boolean not null default false,
  obs text,
  criado_em timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ============================================================
-- ÍNDICES
-- ============================================================
create index on users(workspace_id);
create index on items(workspace_id);
create index on pdv_comandas(workspace_id, status);
create index on pdv_comandas(aberta_em desc);
create index on pdv_itens(comanda_id);
create index on pdv_produtos(workspace_id, ativo);

-- ============================================================
-- FUNÇÕES
-- ============================================================
create or replace function update_last_seen(p_login text, p_workspace_id uuid)
returns void language sql as $$
  update users set last_seen = now()
  where login = p_login and workspace_id = p_workspace_id;
$$;

-- ============================================================
-- PERMISSÕES
-- ============================================================
grant usage on schema public to anon, authenticated;
grant all on all tables in schema public to anon, authenticated;
grant all on all sequences in schema public to anon, authenticated;
grant execute on all functions in schema public to anon, authenticated;

-- ============================================================
-- DADOS INICIAIS
-- ============================================================
insert into workspaces (app_name, plan, modulos)
values ('{{NOME}}', '{{PLANO}}', '{{MODULOS}}')
ON CONFLICT DO NOTHING;

insert into users (workspace_id, login, senha, nome, role, modulos_acesso)
values (
  (select id from workspaces limit 1),
  '{{ADMIN_LOGIN}}',
  '{{ADMIN_HASH}}',
  'Administrador', 'superadmin', '{{MODULOS}}'
);

-- ============================================================
-- MÓDULO ESTOQUE — ContagemFácil
-- ============================================================
create table if not exists contagem_templates (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete cascade,
  titulo text not null, emoji text, color text,
  allowed_users text[], receivers text[],
  items jsonb default '[]',
  created_at timestamptz default now()
);

create table if not exists contagem_submissions (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references workspaces(id) on delete cascade,
  template_id uuid references contagem_templates(id) on delete cascade,
  titulo text, submitted_by text, sent_to text[],
  status text default 'enviada',
  items jsonb default '[]',
  obs_geral text,
  parent_id uuid,
  hidden_by text[],
  updated_at timestamptz default now(),
  completed_by text, completed_at timestamptz,
  created_at timestamptz default now()
);

-- Grants
grant all on contagem_templates to anon;
grant all on contagem_submissions to anon;
