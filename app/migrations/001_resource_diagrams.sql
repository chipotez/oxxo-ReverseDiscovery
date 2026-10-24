-- Run as database owner, never as the web application's restricted role.
CREATE TABLE IF NOT EXISTS resource_diagrams (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 owner_sub text NOT NULL CHECK(length(owner_sub) BETWEEN 1 AND 255),
 name text NOT NULL CHECK(length(name) BETWEEN 1 AND 100),
 document jsonb NOT NULL CHECK(jsonb_typeof(document)='object'),
 revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS resource_diagrams_owner_updated ON resource_diagrams(owner_sub,updated_at DESC);
ALTER TABLE resource_diagrams ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource_diagrams FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS private_diagrams ON resource_diagrams;
CREATE POLICY private_diagrams ON resource_diagrams
 USING (owner_sub=current_setting('koodaria.subject',true))
 WITH CHECK (owner_sub=current_setting('koodaria.subject',true));
REVOKE ALL ON resource_diagrams FROM PUBLIC;
GRANT SELECT,INSERT,UPDATE,DELETE ON resource_diagrams TO koodaria_app;
