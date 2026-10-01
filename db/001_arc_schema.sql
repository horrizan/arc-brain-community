CREATE SCHEMA IF NOT EXISTS n8n;
CREATE SCHEMA IF NOT EXISTS arc;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS arc.items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source text NOT NULL,
    source_ref text,
    item_type text NOT NULL DEFAULT 'unknown',
    title text NOT NULL DEFAULT 'Untitled',
    raw_text text,
    project_key text,
    status text NOT NULL DEFAULT 'inbox',
    priority smallint NOT NULL DEFAULT 0,
    proposal jsonb,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    content_sha256 text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS arc_items_source_hash_uq
ON arc.items(source, content_sha256)
WHERE content_sha256 IS NOT NULL;

CREATE INDEX IF NOT EXISTS arc_items_status_idx ON arc.items(status, created_at DESC);
CREATE INDEX IF NOT EXISTS arc_items_project_idx ON arc.items(project_key, created_at DESC);

CREATE TABLE IF NOT EXISTS arc.agents (
    agent_key text PRIMARY KEY,
    display_name text NOT NULL,
    version text NOT NULL,
    model_role text NOT NULL,
    prompt text NOT NULL,
    enabled boolean NOT NULL DEFAULT true,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS arc.runs (
    id bigserial PRIMARY KEY,
    item_id uuid REFERENCES arc.items(id) ON DELETE CASCADE,
    agent_key text REFERENCES arc.agents(agent_key),
    model_role text,
    model_name text,
    stage text,
    status text NOT NULL DEFAULT 'started',
    input jsonb,
    output jsonb,
    error text,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz
);

CREATE INDEX IF NOT EXISTS arc_runs_item_idx ON arc.runs(item_id, started_at DESC);

CREATE TABLE IF NOT EXISTS arc.approvals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id uuid NOT NULL REFERENCES arc.items(id) ON DELETE CASCADE,
    requested_action text NOT NULL,
    status text NOT NULL DEFAULT 'pending',
    requested_at timestamptz NOT NULL DEFAULT now(),
    decided_at timestamptz,
    decided_by text,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS arc_approvals_pending_idx ON arc.approvals(status, requested_at DESC);

CREATE TABLE IF NOT EXISTS arc.events (
    id bigserial PRIMARY KEY,
    item_id uuid REFERENCES arc.items(id) ON DELETE CASCADE,
    event_type text NOT NULL,
    actor text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS arc_events_item_idx ON arc.events(item_id, created_at DESC);

CREATE TABLE IF NOT EXISTS arc.artifacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id uuid REFERENCES arc.items(id) ON DELETE SET NULL,
    kind text NOT NULL,
    path text,
    sha256 text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION arc.touch_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS arc_items_touch_updated_at ON arc.items;
CREATE TRIGGER arc_items_touch_updated_at
BEFORE UPDATE ON arc.items
FOR EACH ROW EXECUTE FUNCTION arc.touch_updated_at();
