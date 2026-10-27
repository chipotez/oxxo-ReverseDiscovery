BEGIN;
CREATE TABLE diagram_links (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), diagram_id uuid NOT NULL REFERENCES resource_diagrams(id) ON DELETE CASCADE,
 owner_sub text NOT NULL, token_hash text NOT NULL UNIQUE, password_hash text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL DEFAULT now()+interval '1 hour', revoked_at timestamptz,
 CHECK(expires_at<=created_at+interval '1 hour')
);
CREATE TABLE diagram_link_visits (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), link_id uuid NOT NULL REFERENCES diagram_links(id) ON DELETE CASCADE,
 actor_sub text NOT NULL UNIQUE, display_name text NOT NULL, email text NOT NULL,
 joined_at timestamptz NOT NULL DEFAULT now(), last_seen_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE diagram_link_attempts (bucket text PRIMARY KEY, started_at timestamptz NOT NULL DEFAULT now(), attempts integer NOT NULL DEFAULT 1);
CREATE FUNCTION link_lookup(digest text) RETURNS TABLE(id uuid,diagram_id uuid,password_hash text,expires_at timestamptz)
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT l.id,l.diagram_id,l.password_hash,l.expires_at FROM diagram_links l WHERE l.token_hash=digest AND l.revoked_at IS NULL AND l.expires_at>now()
$$;
CREATE FUNCTION link_throttle(target text) RETURNS boolean
 LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 INSERT INTO diagram_link_attempts(bucket) VALUES(target) ON CONFLICT(bucket) DO UPDATE
 SET attempts=CASE WHEN diagram_link_attempts.started_at<now()-interval '10 minutes' THEN 1 ELSE diagram_link_attempts.attempts+1 END,
 started_at=CASE WHEN diagram_link_attempts.started_at<now()-interval '10 minutes' THEN now() ELSE diagram_link_attempts.started_at END
 RETURNING attempts<=10
$$;
CREATE FUNCTION link_throttle_reset(target text) RETURNS void
 LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$ DELETE FROM diagram_link_attempts WHERE bucket=target OR started_at<now()-interval '1 day' $$;
CREATE FUNCTION link_join(target uuid, visitor_name text, visitor_email text) RETURNS TABLE(visit_id uuid,actor_sub text,diagram_id uuid,expires_at timestamptz)
 LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 DECLARE v uuid:=gen_random_uuid(); d uuid; expiry timestamptz;
 BEGIN
 SELECT l.diagram_id,l.expires_at INTO d,expiry FROM diagram_links l WHERE l.id=target AND l.revoked_at IS NULL AND l.expires_at>now() FOR SHARE;
 IF NOT FOUND THEN RETURN; END IF;
 IF length(visitor_name)<2 OR length(visitor_name)>80 OR length(visitor_email)>254 THEN RETURN; END IF;
 INSERT INTO diagram_link_visits(id,link_id,actor_sub,display_name,email) VALUES(v,target,'link:'||v,visitor_name,visitor_email);
 RETURN QUERY SELECT v,'link:'||v,d,expiry;
 END $$;
CREATE FUNCTION link_visit_active(visit uuid, actor text, target uuid) RETURNS boolean
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT EXISTS(SELECT 1 FROM diagram_link_visits v JOIN diagram_links l ON l.id=v.link_id WHERE v.id=visit AND v.actor_sub=actor AND l.diagram_id=target AND l.revoked_at IS NULL AND l.expires_at>now())
$$;
CREATE FUNCTION link_granted(target uuid) RETURNS boolean
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT EXISTS(SELECT 1 FROM diagram_link_visits v JOIN diagram_links l ON l.id=v.link_id WHERE v.actor_sub=current_setting('koodaria.subject',true) AND l.diagram_id=target AND l.revoked_at IS NULL AND l.expires_at>now())
$$;
CREATE OR REPLACE FUNCTION diagram_granted(target uuid) RETURNS boolean
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT link_granted(target) OR EXISTS(SELECT 1 FROM diagram_shares s JOIN workspace_principals p ON p.subject=s.recipient_sub
 WHERE s.diagram_id=target AND s.recipient_sub=current_setting('koodaria.subject',true) AND s.status='active' AND s.permission='edit' AND p.email_verified AND lower(p.email)=s.recipient_email)
$$;
CREATE OR REPLACE FUNCTION diagram_visible(target uuid) RETURNS boolean
 LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT link_granted(target) OR EXISTS(SELECT 1 FROM diagram_shares s JOIN workspace_principals p ON p.subject=s.recipient_sub
 WHERE s.diagram_id=target AND s.recipient_sub=current_setting('koodaria.subject',true) AND s.status='active' AND p.email_verified AND lower(p.email)=s.recipient_email)
$$;
ALTER TABLE diagram_links ENABLE ROW LEVEL SECURITY; ALTER TABLE diagram_links FORCE ROW LEVEL SECURITY;
CREATE POLICY links_owner ON diagram_links USING(owner_sub=current_setting('koodaria.subject',true) AND diagram_owned(diagram_id)) WITH CHECK(owner_sub=current_setting('koodaria.subject',true) AND diagram_owned(diagram_id));
ALTER TABLE diagram_link_visits ENABLE ROW LEVEL SECURITY; ALTER TABLE diagram_link_visits FORCE ROW LEVEL SECURITY;
CREATE POLICY visits_owner ON diagram_link_visits FOR SELECT USING(EXISTS(SELECT 1 FROM diagram_links l WHERE l.id=link_id AND l.owner_sub=current_setting('koodaria.subject',true)));
REVOKE ALL ON FUNCTION link_lookup(text),link_throttle(text),link_throttle_reset(text),link_join(uuid,text,text),link_visit_active(uuid,text,uuid),link_granted(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION link_lookup(text),link_throttle(text),link_throttle_reset(text),link_join(uuid,text,text),link_visit_active(uuid,text,uuid),link_granted(uuid) TO koodaria_app;
GRANT SELECT,INSERT,UPDATE ON diagram_links TO koodaria_app;
GRANT SELECT ON diagram_link_visits TO koodaria_app;
COMMIT;
