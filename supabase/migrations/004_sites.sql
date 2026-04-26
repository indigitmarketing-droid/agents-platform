-- 004_sites.sql

CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    slug TEXT NOT NULL UNIQUE,
    template_kind TEXT NOT NULL CHECK (template_kind IN ('hospitality','service','generic')),
    category TEXT NOT NULL,
    colors JSONB NOT NULL DEFAULT '{}'::jsonb,
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    published_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (lead_id)
);

CREATE INDEX idx_sites_slug ON sites(slug);
CREATE INDEX idx_sites_category ON sites(category);

ALTER PUBLICATION supabase_realtime ADD TABLE sites;

CREATE TRIGGER sites_updated_at
    BEFORE UPDATE ON sites
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
