BEGIN;
CREATE TABLE discovery_connections (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 scope_key text NOT NULL,
 created_by text NOT NULL,
 name text NOT NULL CHECK(length(name) BETWEEN 1 AND 100),
 provider text NOT NULL DEFAULT 'datadog' CHECK(provider='datadog'),
 site text NOT NULL,
 credentials text NOT NULL,
 revision integer NOT NULL DEFAULT 1,
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','testing','failed','verified','saved')),
 run_id uuid,
 stages jsonb NOT NULL DEFAULT '[]',
 sample jsonb NOT NULL DEFAULT '[]',
 sample_total integer NOT NULL DEFAULT 0,
 tested_at timestamptz,
 updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(scope_key,name)
);
ALTER TABLE discovery_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery_connections FORCE ROW LEVEL SECURITY;
CREATE POLICY discovery_scope ON discovery_connections USING(scope_key=component_model_scope()) WITH CHECK(scope_key=component_model_scope());
GRANT SELECT,INSERT,UPDATE,DELETE ON discovery_connections TO koodaria_app;
COMMIT;
