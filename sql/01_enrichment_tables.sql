-- Append-only enrichment tables (SPEC.md section 4.3).
-- IF NOT EXISTS: re-running never drops or empties them.

CREATE TABLE IF NOT EXISTS `{enrichment}.feedback_enrichment` (
  feedback_id STRING,
  category STRING,
  sentiment STRING,
  summary STRING
);

CREATE TABLE IF NOT EXISTS `{enrichment}.feedback_corrections` (
  feedback_id STRING,
  field STRING,
  corrected_value STRING,
  corrected_at TIMESTAMP
);
