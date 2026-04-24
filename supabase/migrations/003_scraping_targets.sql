-- 003_scraping_targets.sql

-- Configurazione target di scraping
CREATE TABLE scraping_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,
    category_type TEXT NOT NULL CHECK (category_type IN ('amenity','shop','craft','leisure','office')),
    city TEXT NOT NULL,
    country_code TEXT NOT NULL,
    timezone TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    last_run_at TIMESTAMPTZ,
    total_leads_found INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (category, city, country_code)
);

CREATE INDEX idx_targets_enabled ON scraping_targets(enabled, last_run_at);

-- Storico esecuzioni
CREATE TABLE scraping_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_id UUID NOT NULL REFERENCES scraping_targets(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','completed','failed')),
    leads_found INT NOT NULL DEFAULT 0,
    leads_new INT NOT NULL DEFAULT 0,
    error TEXT
);

CREATE INDEX idx_runs_target ON scraping_runs(target_id, started_at DESC);

-- Estendi leads (campi nullable, non distruttivo)
ALTER TABLE leads
    ADD COLUMN osm_id TEXT,
    ADD COLUMN category TEXT,
    ADD COLUMN city TEXT,
    ADD COLUMN country_code TEXT,
    ADD COLUMN latitude NUMERIC(9,6),
    ADD COLUMN longitude NUMERIC(9,6);

CREATE UNIQUE INDEX idx_leads_osm_id ON leads(osm_id) WHERE osm_id IS NOT NULL;

-- Realtime per dashboard
ALTER PUBLICATION supabase_realtime ADD TABLE scraping_targets;
ALTER PUBLICATION supabase_realtime ADD TABLE scraping_runs;
