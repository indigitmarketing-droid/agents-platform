-- 007_customer_onboarding.sql
-- E1: multi-tenant schema + future-proof columns for F1 (Stripe)

-- 1. Add owner_user_id to sites (populated by F1 after payment)
ALTER TABLE sites ADD COLUMN owner_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
CREATE INDEX idx_sites_owner_user ON sites(owner_user_id);

-- 2. Add payment fields (used by F1)
ALTER TABLE sites ADD COLUMN published_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE sites ADD COLUMN payment_status TEXT DEFAULT 'unpaid'
  CHECK (payment_status IN ('unpaid', 'paid', 'expired'));
CREATE INDEX idx_sites_payment_grace ON sites(payment_status, published_at);

-- 3. Ensure RLS enabled
ALTER TABLE sites ENABLE ROW LEVEL SECURITY;

-- 4. SELECT policy for authenticated customers — own site only
CREATE POLICY "customers_see_own_site"
  ON sites FOR SELECT
  TO authenticated
  USING (owner_user_id = auth.uid());

-- 5. Block authenticated mutations (service_role bypasses RLS)
CREATE POLICY "no_customer_writes"
  ON sites FOR ALL
  TO authenticated
  USING (false)
  WITH CHECK (false);

-- 6. Public read for anon (used by agents-sites for /s/{slug} rendering)
CREATE POLICY "public_read_sites_by_slug"
  ON sites FOR SELECT
  TO anon
  USING (true);
