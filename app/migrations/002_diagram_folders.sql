BEGIN;
CREATE TABLE IF NOT EXISTS diagram_folders (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 owner_sub text NOT NULL CHECK(length(owner_sub) BETWEEN 1 AND 255),
 name text NOT NULL CHECK(length(name) BETWEEN 1 AND 100),
 revision integer NOT NULL DEFAULT 1,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS diagram_folders_owner_name ON diagram_folders(owner_sub,lower(name));
ALTER TABLE diagram_folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagram_folders FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS private_folders ON diagram_folders;
CREATE POLICY private_folders ON diagram_folders
 USING(owner_sub=current_setting('koodaria.subject',true))
 WITH CHECK(owner_sub=current_setting('koodaria.subject',true));
REVOKE ALL ON diagram_folders FROM PUBLIC;
GRANT SELECT,INSERT,UPDATE,DELETE ON diagram_folders TO koodaria_app;
ALTER TABLE resource_diagrams ADD COLUMN IF NOT EXISTS folder_id uuid REFERENCES diagram_folders(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS resource_diagrams_owner_folder ON resource_diagrams(owner_sub,folder_id);
DROP POLICY IF EXISTS private_diagrams ON resource_diagrams;
CREATE POLICY private_diagrams ON resource_diagrams
 USING(owner_sub=current_setting('koodaria.subject',true))
 WITH CHECK(owner_sub=current_setting('koodaria.subject',true) AND
 (folder_id IS NULL OR EXISTS(SELECT 1 FROM diagram_folders f WHERE f.id=folder_id AND f.owner_sub=resource_diagrams.owner_sub)));
COMMIT;
