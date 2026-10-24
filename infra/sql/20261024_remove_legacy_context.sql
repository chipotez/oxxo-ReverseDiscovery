-- Run after a database backup, with a maintenance role and application stopped.
-- Preserve all other node fields and increment revisions to protect open tabs.
BEGIN;
WITH cleaned AS (
 SELECT d.id,jsonb_set(d.document,'{nodes}',(
  SELECT jsonb_agg(n #- '{data,server_instance,identification,context}' ORDER BY ordinal)
  FROM jsonb_array_elements(d.document->'nodes') WITH ORDINALITY AS nodes(n,ordinal)
 )) AS document
 FROM resource_diagrams d
 WHERE jsonb_path_exists(d.document,'$.nodes[*].data.server_instance.identification.context')
), changed AS (
 UPDATE resource_diagrams d SET document=c.document,revision=d.revision+1,updated_at=now()
 FROM cleaned c WHERE d.id=c.id RETURNING 1
)
SELECT count(*) AS diagrams_cleaned FROM changed;
COMMIT;
