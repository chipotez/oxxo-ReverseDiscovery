BEGIN;
-- Scope derives from the authenticated principal, never a browser parameter.
CREATE FUNCTION component_model_scope() RETURNS text
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT CASE WHEN p.organization_id IS NOT NULL AND p.organization_id<>''
 THEN 'org:'||p.organization_id ELSE 'user:'||p.subject END
 FROM workspace_principals p
 WHERE p.subject=current_setting('koodaria.subject',true) AND p.tier='member'
$$;
REVOKE ALL ON FUNCTION component_model_scope() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION component_model_scope() TO koodaria_app;
CREATE TABLE component_models (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 scope_key text NOT NULL,
 resource_key text NOT NULL,
 revision integer NOT NULL DEFAULT 1 CHECK(revision>=1),
 current_version integer NOT NULL DEFAULT 1 CHECK(current_version>=1),
 created_by text NOT NULL,
 updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(scope_key,resource_key)
);
CREATE TABLE component_model_versions (
 model_id uuid NOT NULL REFERENCES component_models(id),
 version integer NOT NULL CHECK(version>=1),
 schema jsonb NOT NULL CHECK(jsonb_typeof(schema)='object'),
 created_by text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(model_id,version)
);
ALTER TABLE component_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE component_models FORCE ROW LEVEL SECURITY;
ALTER TABLE component_model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE component_model_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY model_scope ON component_models USING(scope_key=component_model_scope()) WITH CHECK(scope_key=component_model_scope());
CREATE POLICY model_version_scope ON component_model_versions USING(EXISTS(SELECT 1 FROM component_models m WHERE m.id=model_id AND m.scope_key=component_model_scope())) WITH CHECK(EXISTS(SELECT 1 FROM component_models m WHERE m.id=model_id AND m.scope_key=component_model_scope()));
GRANT SELECT,INSERT,UPDATE ON component_models TO koodaria_app;
GRANT SELECT,INSERT ON component_model_versions TO koodaria_app;
-- Publications are append-only even for accidental UPDATEs from a migration role.
CREATE FUNCTION immutable_component_version() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Component model versions are immutable'; END $$;
CREATE TRIGGER immutable_component_version BEFORE UPDATE ON component_model_versions FOR EACH ROW EXECUTE FUNCTION immutable_component_version();
COMMIT;
