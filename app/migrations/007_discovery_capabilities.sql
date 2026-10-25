BEGIN;
ALTER TABLE discovery_connections ADD CONSTRAINT discovery_connection_scope_unique UNIQUE(id,scope_key);
CREATE TABLE discovery_capabilities (
 connection_id uuid NOT NULL,
 scope_key text NOT NULL,
 family text NOT NULL,
 status text NOT NULL CHECK(status IN ('available','denied','unavailable','unknown')),
 diagnostics jsonb NOT NULL DEFAULT '{}',
 checked_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(connection_id,family),
 FOREIGN KEY(connection_id,scope_key) REFERENCES discovery_connections(id,scope_key) ON DELETE CASCADE
);
ALTER TABLE discovery_capabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery_capabilities FORCE ROW LEVEL SECURITY;
CREATE POLICY capability_scope ON discovery_capabilities USING(scope_key=component_model_scope()) WITH CHECK(scope_key=component_model_scope());
GRANT SELECT,INSERT,UPDATE,DELETE ON discovery_capabilities TO koodaria_app;
COMMIT;
