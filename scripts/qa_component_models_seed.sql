DO $$ BEGIN IF current_database()<>'koodaria_diagrams_qa' THEN RAISE EXCEPTION 'Disposable QA database required'; END IF; END $$;
CREATE OR REPLACE FUNCTION qa_model_organization(who text, org text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF who NOT LIKE 'qa-model-%' OR org NOT LIKE 'qa-org-%' THEN RAISE EXCEPTION 'Synthetic QA only'; END IF;
 UPDATE workspace_principals SET organization_id=org WHERE subject=who;
END $$;
REVOKE ALL ON FUNCTION qa_model_organization(text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION qa_model_organization(text,text) TO koodaria_app;
