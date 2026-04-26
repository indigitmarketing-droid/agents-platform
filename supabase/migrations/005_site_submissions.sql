-- 005_site_submissions.sql

CREATE TABLE site_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    visitor_name TEXT,
    visitor_email TEXT,
    visitor_phone TEXT,
    message TEXT NOT NULL,
    forwarded_to_email TEXT NOT NULL,
    forwarded_at TIMESTAMPTZ,
    forward_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_submissions_site ON site_submissions(site_id, created_at DESC);

ALTER PUBLICATION supabase_realtime ADD TABLE site_submissions;
