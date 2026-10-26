BEGIN;
ALTER TABLE diagram_shares DROP CONSTRAINT diagram_shares_permission_check;
ALTER TABLE diagram_shares ADD CONSTRAINT diagram_shares_permission_check CHECK(permission IN ('edit','read'));
CREATE OR REPLACE FUNCTION diagram_granted(target uuid) RETURNS boolean
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT EXISTS(SELECT 1 FROM diagram_shares s JOIN workspace_principals p ON p.subject=s.recipient_sub
 WHERE s.diagram_id=target AND s.recipient_sub=current_setting('koodaria.subject',true)
 AND s.status='active' AND s.permission='edit' AND p.email_verified AND lower(p.email)=s.recipient_email)
$$;
CREATE FUNCTION diagram_visible(target uuid) RETURNS boolean
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT EXISTS(SELECT 1 FROM diagram_shares s JOIN workspace_principals p ON p.subject=s.recipient_sub
 WHERE s.diagram_id=target AND s.recipient_sub=current_setting('koodaria.subject',true)
 AND s.status='active' AND p.email_verified AND lower(p.email)=s.recipient_email)
$$;
REVOKE ALL ON FUNCTION diagram_visible(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION diagram_visible(uuid) TO koodaria_app;
DROP POLICY diagram_read ON resource_diagrams;
CREATE POLICY diagram_read ON resource_diagrams FOR SELECT USING(owner_sub=current_setting('koodaria.subject',true) OR diagram_visible(id));

CREATE TABLE diagram_collaborators (
 diagram_id uuid NOT NULL REFERENCES resource_diagrams(id) ON DELETE CASCADE,
 client_id uuid NOT NULL, actor_sub text NOT NULL, display_name text NOT NULL,
 resource_id text, expires_at timestamptz NOT NULL,
 PRIMARY KEY(diagram_id,client_id)
);
CREATE TABLE diagram_operations (
 diagram_id uuid NOT NULL REFERENCES resource_diagrams(id) ON DELETE CASCADE,
 operation_id uuid NOT NULL, actor_sub text NOT NULL, client_id uuid NOT NULL,
 display_name text NOT NULL DEFAULT 'Colaborador', revision integer NOT NULL, changes jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(diagram_id,operation_id), UNIQUE(diagram_id,revision)
);
CREATE TABLE diagram_trash (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), diagram_id uuid NOT NULL REFERENCES resource_diagrams(id) ON DELETE CASCADE,
 operation_id uuid NOT NULL, actor_sub text NOT NULL, resources jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), restored_at timestamptz
);
ALTER TABLE diagram_collaborators ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagram_collaborators FORCE ROW LEVEL SECURITY;
CREATE POLICY collaborators_read ON diagram_collaborators FOR SELECT USING(diagram_owned(diagram_id) OR diagram_visible(diagram_id));
CREATE POLICY collaborators_insert ON diagram_collaborators FOR INSERT WITH CHECK(actor_sub=current_setting('koodaria.subject',true) AND (diagram_owned(diagram_id) OR diagram_visible(diagram_id)));
CREATE POLICY collaborators_update ON diagram_collaborators FOR UPDATE USING(actor_sub=current_setting('koodaria.subject',true)) WITH CHECK(actor_sub=current_setting('koodaria.subject',true));
CREATE POLICY collaborators_delete ON diagram_collaborators FOR DELETE USING(actor_sub=current_setting('koodaria.subject',true) OR diagram_owned(diagram_id));
GRANT SELECT,INSERT,UPDATE,DELETE ON diagram_collaborators TO koodaria_app;
ALTER TABLE diagram_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagram_operations FORCE ROW LEVEL SECURITY;
CREATE POLICY operations_read ON diagram_operations FOR SELECT USING(diagram_owned(diagram_id) OR diagram_visible(diagram_id));
CREATE POLICY operations_insert ON diagram_operations FOR INSERT WITH CHECK(actor_sub=current_setting('koodaria.subject',true) AND (diagram_owned(diagram_id) OR diagram_granted(diagram_id)));
GRANT SELECT,INSERT ON diagram_operations TO koodaria_app;
CREATE INDEX diagram_trash_recent ON diagram_trash(diagram_id,created_at DESC) WHERE restored_at IS NULL;
ALTER TABLE diagram_trash ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagram_trash FORCE ROW LEVEL SECURITY;
CREATE POLICY trash_read ON diagram_trash FOR SELECT USING(diagram_owned(diagram_id));
CREATE POLICY trash_insert ON diagram_trash FOR INSERT WITH CHECK(actor_sub=current_setting('koodaria.subject',true) AND (diagram_owned(diagram_id) OR diagram_granted(diagram_id)));
CREATE POLICY trash_update ON diagram_trash FOR UPDATE USING(diagram_owned(diagram_id)) WITH CHECK(diagram_owned(diagram_id));
GRANT SELECT,INSERT,UPDATE ON diagram_trash TO koodaria_app;
COMMIT;
