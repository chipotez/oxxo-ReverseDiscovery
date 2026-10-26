BEGIN;
CREATE TABLE diagram_comments (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), diagram_id uuid NOT NULL REFERENCES resource_diagrams(id) ON DELETE CASCADE,
 anchor_type text NOT NULL CHECK(anchor_type IN ('node','edge')), anchor_id text NOT NULL CHECK(length(anchor_id) BETWEEN 1 AND 100),
 author_sub text NOT NULL, author_name text NOT NULL, body text NOT NULL CHECK(length(body) BETWEEN 1 AND 2000),
 mentions jsonb NOT NULL DEFAULT '[]', resolved boolean NOT NULL DEFAULT false, revision integer NOT NULL DEFAULT 1,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX diagram_comments_anchor ON diagram_comments(diagram_id,anchor_type,anchor_id,created_at);
ALTER TABLE diagram_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagram_comments FORCE ROW LEVEL SECURITY;
CREATE POLICY comments_read ON diagram_comments FOR SELECT USING(diagram_owned(diagram_id) OR diagram_visible(diagram_id));
CREATE POLICY comments_create ON diagram_comments FOR INSERT WITH CHECK(author_sub=current_setting('koodaria.subject',true) AND (diagram_owned(diagram_id) OR diagram_granted(diagram_id)));
CREATE POLICY comments_update ON diagram_comments FOR UPDATE USING(diagram_owned(diagram_id) OR diagram_granted(diagram_id)) WITH CHECK(diagram_owned(diagram_id) OR diagram_granted(diagram_id));
GRANT SELECT,INSERT,UPDATE ON diagram_comments TO koodaria_app;
CREATE FUNCTION diagram_comment_people(target uuid) RETURNS TABLE(subject text,display_name text)
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT p.subject,p.display_name FROM workspace_principals p JOIN resource_diagrams d ON d.owner_sub=p.subject
 WHERE d.id=target AND (diagram_owned(target) OR diagram_visible(target))
 UNION SELECT p.subject,p.display_name FROM workspace_principals p JOIN diagram_shares s ON s.recipient_sub=p.subject
 WHERE s.diagram_id=target AND s.status='active' AND p.email_verified AND lower(p.email)=s.recipient_email AND (diagram_owned(target) OR diagram_visible(target))
$$;
REVOKE ALL ON FUNCTION diagram_comment_people(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION diagram_comment_people(uuid) TO koodaria_app;
COMMIT;
