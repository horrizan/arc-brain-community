CREATE TABLE IF NOT EXISTS arc.projects (
    project_key text PRIMARY KEY,
    display_name text NOT NULL,
    priority_weight integer NOT NULL DEFAULT 0,
    lifecycle text NOT NULL DEFAULT 'active',
    objective text NOT NULL,
    policy text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Project rows are loaded from config/projects.json by scripts/sync_projects.py.

CREATE TABLE IF NOT EXISTS arc.outreach (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_key text REFERENCES arc.projects(project_key),
    item_id uuid REFERENCES arc.items(id) ON DELETE SET NULL,
    recipient_name text,
    recipient_email text,
    organization text,
    channel text NOT NULL DEFAULT 'email',
    reason_to_contact text,
    source_context jsonb NOT NULL DEFAULT '{}'::jsonb,
    subject text,
    draft_body text,
    status text NOT NULL DEFAULT 'draft',
    approval_required boolean NOT NULL DEFAULT true,
    approved_at timestamptz,
    approved_by text,
    sent_at timestamptz,
    send_result jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS arc_outreach_status_idx ON arc.outreach(status, created_at DESC);
CREATE INDEX IF NOT EXISTS arc_outreach_project_idx ON arc.outreach(project_key, created_at DESC);

CREATE TABLE IF NOT EXISTS arc.research_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id uuid REFERENCES arc.items(id) ON DELETE CASCADE,
    project_key text REFERENCES arc.projects(project_key),
    question text NOT NULL,
    status text NOT NULL DEFAULT 'queued',
    source_urls jsonb NOT NULL DEFAULT '[]'::jsonb,
    findings jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS arc_research_status_idx ON arc.research_tasks(status, created_at DESC);

DROP TRIGGER IF EXISTS arc_outreach_touch_updated_at ON arc.outreach;
CREATE TRIGGER arc_outreach_touch_updated_at
BEFORE UPDATE ON arc.outreach
FOR EACH ROW EXECUTE FUNCTION arc.touch_updated_at();

DROP TRIGGER IF EXISTS arc_research_touch_updated_at ON arc.research_tasks;
CREATE TRIGGER arc_research_touch_updated_at
BEFORE UPDATE ON arc.research_tasks
FOR EACH ROW EXECUTE FUNCTION arc.touch_updated_at();

CREATE TABLE IF NOT EXISTS arc.settings (
    key text PRIMARY KEY,
    value jsonb NOT NULL,
    description text,
    updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO arc.settings(key,value,description)
VALUES ('outreach_send_enabled','false'::jsonb,'Master kill switch for automated outbound email. Keep false until transport and approval policy are tested.')
ON CONFLICT(key) DO NOTHING;
INSERT INTO arc.settings(key,value,description)
VALUES ('smtp_from','""'::jsonb,'From address used by ARC-05 when SMTP sending is enabled.')
ON CONFLICT(key) DO NOTHING;
