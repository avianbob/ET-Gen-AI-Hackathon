-- PharmAI / Repurpose — Supabase schema
-- Run in Supabase Dashboard → SQL Editor (paste → Run).
-- Then run 002_seed.sql (optional).

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    integration_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    api_key_encrypted TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, integration_name)
);

CREATE INDEX IF NOT EXISTS idx_user_integrations_user_id ON public.user_integrations (user_id);

CREATE TABLE IF NOT EXISTS public.search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,
    session_id TEXT NOT NULL DEFAULT '',
    drug_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    execution_time DOUBLE PRECISION NOT NULL DEFAULT 0,
    cached BOOLEAN NOT NULL DEFAULT FALSE,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    indications_count INTEGER NOT NULL DEFAULT 0,
    top_indication TEXT,
    top_confidence DOUBLE PRECISION,
    results JSONB
);

CREATE INDEX IF NOT EXISTS idx_search_history_user_created ON public.search_history (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_history_drug ON public.search_history (drug_name);

CREATE TABLE IF NOT EXISTS public.saved_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    drug_name TEXT,
    indication TEXT,
    status TEXT NOT NULL DEFAULT 'saved',
    notes TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_saved_opportunities_user ON public.saved_opportunities (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS public.market_data_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    indication TEXT NOT NULL UNIQUE,
    market_size_usd NUMERIC,
    cagr NUMERIC,
    patient_population BIGINT,
    geographic_breakdown JSONB,
    key_players JSONB,
    data_source TEXT,
    cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_data_cache_expires ON public.market_data_cache (expires_at);

-- ---------------------------------------------------------------------------
-- updated_at trigger
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS tr_user_integrations_updated ON public.user_integrations;
CREATE TRIGGER tr_user_integrations_updated
    BEFORE UPDATE ON public.user_integrations
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS tr_saved_opportunities_updated ON public.saved_opportunities;
CREATE TRIGGER tr_saved_opportunities_updated
    BEFORE UPDATE ON public.saved_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- RPCs (used by repurpose/database/supabase_client.py)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.increment_integration_usage(integration_id UUID)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    UPDATE public.user_integrations
    SET usage_count = usage_count + 1,
        last_used_at = NOW()
    WHERE id = integration_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.get_popular_drugs(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (drug_name TEXT, search_count BIGINT)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT sh.drug_name, COUNT(*)::BIGINT AS search_count
    FROM public.search_history sh
    GROUP BY sh.drug_name
    ORDER BY search_count DESC
    LIMIT COALESCE(NULLIF(limit_count, 0), 10);
$$;

GRANT EXECUTE ON FUNCTION public.increment_integration_usage(UUID) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_popular_drugs(INTEGER) TO anon, authenticated, service_role;

-- ---------------------------------------------------------------------------
-- RLS (publishable/anon key from FastAPI needs policies)
-- Tighten later: auth.uid() + JWT, or use service_role only on the server.
-- ---------------------------------------------------------------------------
ALTER TABLE public.user_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.market_data_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "user_integrations_all_anon" ON public.user_integrations;
DROP POLICY IF EXISTS "user_integrations_all_authenticated" ON public.user_integrations;
CREATE POLICY "user_integrations_all_anon"
    ON public.user_integrations FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "user_integrations_all_authenticated"
    ON public.user_integrations FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "search_history_all_anon" ON public.search_history;
DROP POLICY IF EXISTS "search_history_all_authenticated" ON public.search_history;
CREATE POLICY "search_history_all_anon"
    ON public.search_history FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "search_history_all_authenticated"
    ON public.search_history FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "saved_opportunities_all_anon" ON public.saved_opportunities;
DROP POLICY IF EXISTS "saved_opportunities_all_authenticated" ON public.saved_opportunities;
CREATE POLICY "saved_opportunities_all_anon"
    ON public.saved_opportunities FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "saved_opportunities_all_authenticated"
    ON public.saved_opportunities FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "market_data_cache_all_anon" ON public.market_data_cache;
DROP POLICY IF EXISTS "market_data_cache_all_authenticated" ON public.market_data_cache;
CREATE POLICY "market_data_cache_all_anon"
    ON public.market_data_cache FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "market_data_cache_all_authenticated"
    ON public.market_data_cache FOR ALL TO authenticated USING (true) WITH CHECK (true);
