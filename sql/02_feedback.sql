-- One row per feedback item: ratings and chats in one shape (SPEC.md section 4.2).
-- Rules in sql/SPEC.md section 2.

CREATE OR REPLACE VIEW `{clean}.feedback` AS

-- Shape: both sources mapped to the same columns, types with SAFE_CAST.
WITH ratings AS (
  SELECT
    CONCAT('web_rating:', review_id) AS feedback_id,
    'web_rating' AS source_channel,
    order_id,
    product_id,
    SAFE_CAST(stars AS INT64) AS stars,
    comment AS text,
    SAFE_CAST(created_at AS TIMESTAMP) AS created_at
  FROM `{raw}.web_rating`
),

chats AS (
  SELECT
    CONCAT('support_chat:', chat_id) AS feedback_id,
    'support_chat' AS source_channel,
    order_id,
    CAST(NULL AS STRING) AS product_id,
    CAST(NULL AS INT64) AS stars,
    transcript AS text,
    SAFE_CAST(started_at AS TIMESTAMP) AS created_at
  FROM `{raw}.support_chat`
),

-- Validation: ratings with stars outside 1-5 are removed.
valid AS (
  SELECT * FROM ratings WHERE stars BETWEEN 1 AND 5
  UNION ALL
  SELECT * FROM chats
),

-- Deduplication, after validation: one row per feedback_id, chosen arbitrarily.
deduplicated AS (
  SELECT *
  FROM valid
  QUALIFY ROW_NUMBER() OVER (PARTITION BY feedback_id) = 1
)

-- Order fields; a chat takes its product_id from the order.
SELECT
  f.feedback_id,
  f.source_channel,
  f.order_id,
  IF(f.source_channel = 'support_chat', o.product_id, f.product_id) AS product_id,
  o.product_name,
  o.customer_id,
  SAFE_CAST(o.returned AS BOOL) AS returned,
  f.stars,
  f.text,
  f.created_at
FROM deduplicated AS f
LEFT JOIN `{raw}.orders` AS o
  ON o.order_id = f.order_id
