-- One row per feedback item, with AI output and human corrections (SPEC.md section 4.2).
-- Rules in sql/SPEC.md section 3.

CREATE OR REPLACE VIEW `{clean}.feedback_workbench` AS

-- Only the most recent correction per item and field.
WITH latest_corrections AS (
  SELECT feedback_id, field, corrected_value
  FROM `{enrichment}.feedback_corrections`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY feedback_id, field ORDER BY corrected_at DESC) = 1
)

-- Current value: the latest correction if present, otherwise the AI value.
SELECT
  f.*,
  COALESCE(cc.corrected_value, e.category) AS category,
  COALESCE(cs.corrected_value, e.sentiment) AS sentiment,
  e.summary,
  e.category AS ai_category,
  e.sentiment AS ai_sentiment,
  (cc.feedback_id IS NOT NULL OR cs.feedback_id IS NOT NULL) AS is_corrected
FROM `{clean}.feedback` AS f
LEFT JOIN `{enrichment}.feedback_enrichment` AS e
  ON e.feedback_id = f.feedback_id
LEFT JOIN latest_corrections AS cc
  ON cc.feedback_id = f.feedback_id AND cc.field = 'category'
LEFT JOIN latest_corrections AS cs
  ON cs.feedback_id = f.feedback_id AND cs.field = 'sentiment'
