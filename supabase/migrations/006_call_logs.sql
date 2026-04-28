-- 006_call_logs.sql

CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    call_type TEXT NOT NULL CHECK (call_type IN ('cold_call', 'site_ready_call')),
    agent_id TEXT NOT NULL,
    call_sid TEXT,
    conversation_id TEXT,
    phone TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'initiated'
        CHECK (status IN ('initiated', 'in_progress', 'completed', 'failed', 'no_answer', 'busy')),
    outcome TEXT CHECK (outcome IN ('accepted', 'rejected', 'unclear')),
    transcript TEXT,
    duration_seconds INT,
    audio_url TEXT,
    call_brief JSONB,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    analyzed_at TIMESTAMPTZ,
    error TEXT
);

CREATE INDEX idx_call_logs_lead ON call_logs(lead_id, started_at DESC);
CREATE INDEX idx_call_logs_status ON call_logs(status);
CREATE INDEX idx_call_logs_call_sid ON call_logs(call_sid) WHERE call_sid IS NOT NULL;
CREATE INDEX idx_call_logs_conversation ON call_logs(conversation_id) WHERE conversation_id IS NOT NULL;

CREATE TABLE do_not_call (
    phone TEXT PRIMARY KEY,
    reason TEXT NOT NULL CHECK (reason IN ('lead_request', 'manual', 'invalid_number', 'dnc_api_match', 'max_attempts')),
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

ALTER TABLE leads
    ADD COLUMN call_status TEXT NOT NULL DEFAULT 'never_called'
        CHECK (call_status IN ('never_called','called','accepted','rejected','do_not_call')),
    ADD COLUMN last_called_at TIMESTAMPTZ,
    ADD COLUMN call_attempts INT NOT NULL DEFAULT 0;

CREATE INDEX idx_leads_call_status ON leads(call_status, last_called_at);

ALTER PUBLICATION supabase_realtime ADD TABLE call_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE do_not_call;
