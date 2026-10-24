BEGIN;
CREATE TABLE resource_standards (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 owner_sub text NOT NULL,
 name text NOT NULL,
 revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
 draft jsonb NOT NULL,
 published_version integer NOT NULL DEFAULT 0 CHECK(published_version>=0),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX standard_owner_name ON resource_standards(owner_sub,lower(name));
ALTER TABLE resource_standards ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource_standards FORCE ROW LEVEL SECURITY;
CREATE POLICY private_standards ON resource_standards USING(workspace_member() AND owner_sub=current_setting('koodaria.subject',true)) WITH CHECK(workspace_member() AND owner_sub=current_setting('koodaria.subject',true));
GRANT SELECT,INSERT,UPDATE ON resource_standards TO koodaria_app;
CREATE TABLE resource_standard_versions (
 standard_id uuid NOT NULL REFERENCES resource_standards(id),
 version integer NOT NULL CHECK(version>0),
 owner_sub text NOT NULL,
 definition jsonb NOT NULL,
 published_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(standard_id,version)
);
ALTER TABLE resource_standard_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource_standard_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY private_standard_versions ON resource_standard_versions FOR SELECT USING(workspace_member() AND owner_sub=current_setting('koodaria.subject',true));
CREATE POLICY publish_own_standard ON resource_standard_versions FOR INSERT WITH CHECK(workspace_member() AND owner_sub=current_setting('koodaria.subject',true) AND EXISTS(SELECT 1 FROM resource_standards s WHERE s.id=standard_id AND s.owner_sub=resource_standard_versions.owner_sub));
GRANT SELECT,INSERT ON resource_standard_versions TO koodaria_app;
COMMIT;
