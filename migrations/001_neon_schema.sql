CREATE TABLE IF NOT EXISTS leads(
  id BIGSERIAL PRIMARY KEY,
  company_name TEXT NOT NULL UNIQUE,
  website TEXT DEFAULT '', city TEXT DEFAULT '', country TEXT DEFAULT '',
  industry TEXT DEFAULT '', contact_name TEXT DEFAULT '', contact_email TEXT DEFAULT '',
  source TEXT DEFAULT '', owner TEXT DEFAULT '', rating DOUBLE PRECISION DEFAULT 0,
  reviews INTEGER DEFAULT 0, status TEXT NOT NULL DEFAULT 'New', notes TEXT DEFAULT '',
  deal_value DOUBLE PRECISION DEFAULT 0, probability DOUBLE PRECISION DEFAULT 0,
  next_action TEXT DEFAULT '', follow_up_date TEXT DEFAULT '', last_contacted_at TEXT DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, project_name TEXT NOT NULL,
  objective TEXT DEFAULT '', stage TEXT DEFAULT 'Discovery', brief TEXT DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audits(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, url TEXT NOT NULL,
  audited_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), overall INTEGER, technical INTEGER,
  content INTEGER, conversion INTEGER, measurement INTEGER, payload_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS websites(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  bundle_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS proposals(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), proposal_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_log(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, action TEXT NOT NULL, detail TEXT DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS intelligence_runs(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  provider TEXT NOT NULL, model TEXT DEFAULT '', diagnosis_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS content_runs(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  provider TEXT NOT NULL, content_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS outreach_runs(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  channel TEXT NOT NULL, subject TEXT DEFAULT '', body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Draft', source_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS proposal_versions(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  version_no INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'Draft', proposal_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales_events(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, event_type TEXT NOT NULL,
  event_date TIMESTAMPTZ NOT NULL DEFAULT NOW(), notes TEXT DEFAULT '', deal_value DOUBLE PRECISION DEFAULT 0
);

CREATE TABLE IF NOT EXISTS users(
  id BIGSERIAL PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'admin', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), last_login_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS agent_runs(
  id BIGSERIAL PRIMARY KEY, run_id TEXT NOT NULL, lead_id BIGINT NOT NULL, agent TEXT NOT NULL,
  status TEXT NOT NULL, output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb, next_action TEXT DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_agent_runs_lead_run ON agent_runs(lead_id, run_id);

CREATE TABLE IF NOT EXISTS workflow_runs(
  id BIGSERIAL PRIMARY KEY, run_id TEXT NOT NULL UNIQUE, lead_id BIGINT NOT NULL,
  decision TEXT DEFAULT '', decision_reason TEXT DEFAULT '', current_stage TEXT DEFAULT 'Discovery',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS human_approvals(
  id BIGSERIAL PRIMARY KEY, run_id TEXT NOT NULL, lead_id BIGINT NOT NULL,
  action TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending', approved_by TEXT DEFAULT '', note TEXT DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS delivery_records(
  id BIGSERIAL PRIMARY KEY, lead_id BIGINT NOT NULL, project_id BIGINT,
  deliverable_type TEXT NOT NULL, file_name TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Draft',
  revenue_amount DOUBLE PRECISION DEFAULT 0, delivered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS ix_sales_events_date ON sales_events(event_date);
