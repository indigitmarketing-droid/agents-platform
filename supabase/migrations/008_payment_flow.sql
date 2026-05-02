-- 008_payment_flow.sql
-- F1 (Stripe payments) + D-Phase2 (sales call) tracking

-- 1. Stripe-specific fields on sites
ALTER TABLE sites ADD COLUMN stripe_checkout_session_id TEXT;
ALTER TABLE sites ADD COLUMN stripe_payment_intent_id TEXT;
ALTER TABLE sites ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE sites ADD COLUMN paid_at TIMESTAMPTZ;
CREATE INDEX idx_sites_stripe_session ON sites(stripe_checkout_session_id);
CREATE INDEX idx_sites_stripe_pi ON sites(stripe_payment_intent_id);

-- 2. D-Phase2 retry tracking
ALTER TABLE sites ADD COLUMN sales_call_attempts INT NOT NULL DEFAULT 0;
ALTER TABLE sites ADD COLUMN last_sales_call_at TIMESTAMPTZ;
ALTER TABLE sites ADD COLUMN sales_call_outcome TEXT
  CHECK (sales_call_outcome IS NULL OR sales_call_outcome IN
    ('accepted_pay', 'interested_no_call', 'rejected', 'no_answer', 'busy', 'unclear'));

-- 3. Stripe events table (audit + dedupe + replay)
CREATE TABLE stripe_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stripe_event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    site_id UUID REFERENCES sites(id) ON DELETE SET NULL,
    processed_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_stripe_events_type ON stripe_events(event_type, created_at DESC);
CREATE INDEX idx_stripe_events_site ON stripe_events(site_id);

-- 4. Service role bypasses RLS, but enable RLS on stripe_events for safety
ALTER TABLE stripe_events ENABLE ROW LEVEL SECURITY;
