BEGIN;
CREATE TABLE IF NOT EXISTS workspace_principals (
 subject text PRIMARY KEY,
 tier text NOT NULL DEFAULT 'guest' CHECK(tier IN ('member','guest')),
 email text,
 email_verified boolean NOT NULL DEFAULT false,
 display_name text NOT NULL DEFAULT '',
 organization_id text,
 last_login_at timestamptz NOT NULL DEFAULT now()
);
-- Preserve current owners as full members. New, unknown identities are guests.
INSERT INTO workspace_principals(subject,tier)
 SELECT owner_sub,'member' FROM resource_diagrams
 UNION SELECT owner_sub,'member' FROM diagram_folders
 ON CONFLICT(subject) DO NOTHING;
ALTER TABLE workspace_principals ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_principals FORCE ROW LEVEL SECURITY;
CREATE POLICY principal_read ON workspace_principals FOR SELECT USING(subject=current_setting('koodaria.subject',true));
CREATE POLICY principal_create ON workspace_principals FOR INSERT WITH CHECK(subject=current_setting('koodaria.subject',true) AND tier='guest');
CREATE POLICY principal_update ON workspace_principals FOR UPDATE USING(subject=current_setting('koodaria.subject',true)) WITH CHECK(subject=current_setting('koodaria.subject',true));
GRANT SELECT,INSERT ON workspace_principals TO koodaria_app;
GRANT UPDATE(email,email_verified,display_name,last_login_at) ON workspace_principals TO koodaria_app;
CREATE TABLE IF NOT EXISTS diagram_shares (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 diagram_id uuid NOT NULL REFERENCES resource_diagrams(id) ON DELETE CASCADE,
 owner_sub text NOT NULL,
 recipient_email text NOT NULL CHECK(length(recipient_email) BETWEEN 3 AND 254),
 recipient_sub text,
 permission text NOT NULL DEFAULT 'edit' CHECK(permission='edit'),
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','active','revoked','delivery_failed')),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL DEFAULT (now()+interval '7 days'),
 last_sent_at timestamptz,
 UNIQUE(diagram_id,recipient_email)
);
CREATE INDEX IF NOT EXISTS diagram_shares_recipient ON diagram_shares(recipient_sub,diagram_id) WHERE status='active';
CREATE TABLE IF NOT EXISTS diagram_audit (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 diagram_id uuid NOT NULL,
 actor_sub text NOT NULL,
 action text NOT NULL CHECK(action IN ('share','revoke','edit')),
 created_at timestamptz NOT NULL DEFAULT now()
);
-- Small definer functions avoid RLS recursion. Their owner is the migration role,
-- never the application role. No dynamic SQL or client-provided identity.
CREATE OR REPLACE FUNCTION workspace_member() RETURNS boolean
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT EXISTS(SELECT 1 FROM workspace_principals WHERE subject=current_setting('koodaria.subject',true) AND tier='member')
$$;
CREATE OR REPLACE FUNCTION diagram_owned(target uuid) RETURNS boolean
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT EXISTS(SELECT 1 FROM resource_diagrams WHERE id=target AND owner_sub=current_setting('koodaria.subject',true))
$$;
CREATE OR REPLACE FUNCTION diagram_granted(target uuid) RETURNS boolean
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT EXISTS(SELECT 1 FROM diagram_shares s JOIN workspace_principals p ON p.subject=s.recipient_sub
 WHERE s.diagram_id=target AND s.recipient_sub=current_setting('koodaria.subject',true)
 AND s.status='active' AND p.email_verified AND lower(p.email)=s.recipient_email)
$$;
CREATE OR REPLACE FUNCTION principal_by_email(target text) RETURNS TABLE(subject text,email_verified boolean,tier text)
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT p.subject,p.email_verified,p.tier FROM workspace_principals p
 WHERE lower(p.email)=target AND p.email_verified AND workspace_member() LIMIT 2
$$;
CREATE OR REPLACE FUNCTION activate_diagram_invites() RETURNS void
 LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 UPDATE diagram_shares s SET status='active',updated_at=now()
 FROM workspace_principals p WHERE p.subject=current_setting('koodaria.subject',true)
 AND p.email_verified AND lower(p.email)=s.recipient_email AND s.recipient_sub=p.subject
 AND s.status='pending' AND s.expires_at>now()
$$;
REVOKE ALL ON FUNCTION workspace_member(),diagram_owned(uuid),diagram_granted(uuid),principal_by_email(text),activate_diagram_invites() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION workspace_member(),diagram_owned(uuid),diagram_granted(uuid),principal_by_email(text),activate_diagram_invites() TO koodaria_app;
ALTER TABLE diagram_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagram_shares FORCE ROW LEVEL SECURITY;
CREATE POLICY share_read ON diagram_shares FOR SELECT USING(owner_sub=current_setting('koodaria.subject',true) OR recipient_sub=current_setting('koodaria.subject',true));
CREATE POLICY share_insert ON diagram_shares FOR INSERT WITH CHECK(workspace_member() AND owner_sub=current_setting('koodaria.subject',true) AND diagram_owned(diagram_id));
CREATE POLICY share_update ON diagram_shares FOR UPDATE USING(owner_sub=current_setting('koodaria.subject',true) AND diagram_owned(diagram_id)) WITH CHECK(owner_sub=current_setting('koodaria.subject',true) AND diagram_owned(diagram_id));
GRANT SELECT,INSERT,UPDATE ON diagram_shares TO koodaria_app;
ALTER TABLE diagram_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagram_audit FORCE ROW LEVEL SECURITY;
CREATE POLICY audit_insert ON diagram_audit FOR INSERT WITH CHECK(actor_sub=current_setting('koodaria.subject',true) AND (diagram_owned(diagram_id) OR diagram_granted(diagram_id)));
GRANT INSERT ON diagram_audit TO koodaria_app;
GRANT USAGE ON SEQUENCE diagram_audit_id_seq TO koodaria_app;
DROP POLICY private_diagrams ON resource_diagrams;
CREATE POLICY diagram_read ON resource_diagrams FOR SELECT USING(owner_sub=current_setting('koodaria.subject',true) OR diagram_granted(id));
CREATE POLICY diagram_create ON resource_diagrams FOR INSERT WITH CHECK(workspace_member() AND owner_sub=current_setting('koodaria.subject',true) AND (folder_id IS NULL OR EXISTS(SELECT 1 FROM diagram_folders f WHERE f.id=folder_id AND f.owner_sub=resource_diagrams.owner_sub)));
CREATE POLICY diagram_edit ON resource_diagrams FOR UPDATE USING(owner_sub=current_setting('koodaria.subject',true) OR diagram_granted(id)) WITH CHECK((owner_sub=current_setting('koodaria.subject',true) AND (folder_id IS NULL OR EXISTS(SELECT 1 FROM diagram_folders f WHERE f.id=folder_id AND f.owner_sub=resource_diagrams.owner_sub))) OR diagram_granted(id));
CREATE POLICY diagram_delete ON resource_diagrams FOR DELETE USING(owner_sub=current_setting('koodaria.subject',true));
CREATE OR REPLACE FUNCTION protect_shared_diagram_metadata() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
BEGIN
 IF OLD.owner_sub<>current_setting('koodaria.subject',true) AND
 (NEW.owner_sub<>OLD.owner_sub OR NEW.folder_id IS DISTINCT FROM OLD.folder_id OR NEW.id<>OLD.id) THEN
  RAISE insufficient_privilege USING MESSAGE='Shared diagram metadata is immutable';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER protect_shared_metadata BEFORE UPDATE ON resource_diagrams FOR EACH ROW EXECUTE FUNCTION protect_shared_diagram_metadata();
DROP POLICY private_folders ON diagram_folders;
CREATE POLICY private_folders ON diagram_folders USING(workspace_member() AND owner_sub=current_setting('koodaria.subject',true)) WITH CHECK(workspace_member() AND owner_sub=current_setting('koodaria.subject',true));
COMMIT;
