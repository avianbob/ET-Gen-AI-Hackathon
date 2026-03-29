-- Optional seed data (idempotent where possible). Run after 001_schema.sql.

-- Demo user id for local / anonymous-style rows (align with your app’s user_id when you add auth)
-- ---------------------------------------------------------------------------
INSERT INTO public.user_integrations (user_id, integration_name, is_active, usage_count, config)
VALUES
    ('demo-local', 'literature', true, 0, '{"source": "seed"}'::jsonb),
    ('demo-local', 'clinical_trials', true, 0, '{"source": "seed"}'::jsonb),
    ('demo-local', 'patent', true, 0, '{"source": "seed"}'::jsonb)
ON CONFLICT (user_id, integration_name) DO NOTHING;

-- Sample search history (powers get_popular_drugs)
INSERT INTO public.search_history (
    user_id, session_id, drug_name, execution_time, cached, evidence_count, indications_count,
    top_indication, top_confidence
)
VALUES
    ('demo-local', 'seed-session-1', 'Metformin', 12.5, false, 24, 5, 'Type 2 Diabetes', 0.88),
    ('demo-local', 'seed-session-2', 'Metformin', 8.1, true, 18, 4, 'PCOS', 0.72),
    ('demo-local', 'seed-session-3', 'Aspirin', 15.2, false, 30, 6, 'Cardiovascular prevention', 0.81),
    (NULL, 'seed-anon-1', 'Sildenafil', 20.0, false, 12, 3, 'Pulmonary arterial hypertension', 0.65);

-- Sample saved opportunity
INSERT INTO public.saved_opportunities (user_id, drug_name, indication, status, notes, payload)
VALUES (
    'demo-local',
    'Metformin',
    'Longevity / anti-aging research',
    'saved',
    'Seeded example — replace with real saves from the UI.',
    '{"composite_score": 72, "source": "seed"}'::jsonb
);

-- Sample market cache row (30-day TTL from seed run time)
INSERT INTO public.market_data_cache (
    indication, market_size_usd, cagr, patient_population,
    geographic_breakdown, key_players, data_source, expires_at
)
VALUES (
    'Type 2 Diabetes',
    125000000000,
    4.2,
    450000000,
    '{"North America": 0.35, "Europe": 0.28, "Asia Pacific": 0.30}'::jsonb,
    '["Novo Nordisk", "Eli Lilly", "Sanofi"]'::jsonb,
    'seed / illustrative',
    NOW() + INTERVAL '30 days'
)
ON CONFLICT (indication) DO UPDATE SET
    market_size_usd = EXCLUDED.market_size_usd,
    cagr = EXCLUDED.cagr,
    patient_population = EXCLUDED.patient_population,
    geographic_breakdown = EXCLUDED.geographic_breakdown,
    key_players = EXCLUDED.key_players,
    data_source = EXCLUDED.data_source,
    cached_at = NOW(),
    expires_at = EXCLUDED.expires_at;
