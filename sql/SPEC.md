# sql — SPEC

Defines the clean views and the empty enrichment tables in BigQuery
(`SPEC.md` §4.2, §4.3). Uses names from `config.py`.

## 1. Interface

`python -m sql.apply`

Runs the `.sql` files in `sql/` in name order, one query job each:

| File | Creates |
|---|---|
| `01_enrichment_tables.sql` | `enrichment.feedback_enrichment`, `enrichment.feedback_corrections` with `CREATE TABLE IF NOT EXISTS`; columns and types from `SPEC.md` §4.3 |
| `02_feedback.sql` | `clean.feedback` with `CREATE OR REPLACE VIEW` |
| `03_feedback_workbench.sql` | `clean.feedback_workbench` with `CREATE OR REPLACE VIEW` |

- The SQL files contain no project or dataset names. They refer to tables as
  `{raw}.<table>`, `{clean}.<table>` and `{enrichment}.<table>`; before running
  a file, `sql.apply` replaces each placeholder with `<PROJECT_ID>.<dataset name>`
  from `config.py` (e.g. `{raw}.web_rating` →
  `aura-feedback-workbench-510309.raw.web_rating`).
- Safe to re-run: tables are never dropped or emptied; views are replaced with
  the current definition.
- Any failure stops the run with the error.

**Prerequisite:** datasets exist and the raw tables are loaded (`SPEC.md` §3,
run order).
**Dependencies:** `google-cloud-bigquery`.

## 2. `clean.feedback`

Built in three steps, in this order:

1. **Shape.** Ratings and chats are mapped to the same columns (`SPEC.md` §4.2),
   so they can be stacked in one view. Raw values are STRING and are converted
   to the types of §4.2 with `SAFE_CAST`: a value that cannot be converted
   becomes NULL instead of failing the whole view.
2. **Validation.** Ratings whose `stars` is not from 1 to 5 are removed from the
   view (they stay in raw).
3. **Deduplication.** One row per `feedback_id` is kept, chosen arbitrarily:
   duplicates are copies of the same line. It runs after validation, so an
   invalid copy never replaces a valid one.

Only the dirty rows of `data_gen` §4 are handled; any other value is assumed
valid.

Then each row is joined to `raw.orders` on `order_id` (one row per order,
`data_gen` §2) for `customer_id`, `product_name`, `returned` and a chat's
`product_id`.

## 3. `clean.feedback_workbench`

`clean.feedback` joined, with `LEFT JOIN`, to:

- **`enrichment.feedback_enrichment`** on `feedback_id`, for `ai_category`,
  `ai_sentiment` and `summary`. There is at most one row per item
  (`SPEC.md` §4.3), so the join never multiplies rows.
- **`enrichment.feedback_corrections`**, which can hold several corrections per
  item and field: for each item and `field`, only the most recent one (latest
  `corrected_at`) is used.

Then:

- `category` = the latest `category` correction if present, otherwise
  `ai_category`; the same for `sentiment`.
- `is_corrected` = the item has at least one correction, on either field.

## 4. Verified by

Run `python -m sql.apply` after the first load (`SPEC.md` §3), then check:

- The two enrichment tables and the two views exist.
- `clean.feedback`:
  - each `feedback_id` appears once;
  - no rating has `stars` outside 1–5;
  - row count = distinct `review_id` among ratings with `stars` from 1 to 5 +
    distinct `chat_id`;
  - ratings without a comment are present with `text` NULL; chats have
    `stars` NULL;
  - `customer_id`, `product_name` and `returned` are never NULL.
- `clean.feedback_workbench`: same row count as `clean.feedback`;
  `ai_category`, `ai_sentiment`, `summary`, `category` and `sentiment` are NULL
  and `is_corrected` is false.
- Correction logic: insert two `category` corrections for one feedback item, a
  few seconds apart, as the app would. In `clean.feedback_workbench` that item
  has `category` = the second value, `is_corrected` true, `ai_category` and
  `sentiment` unchanged; every other item has `is_corrected` false.
- A second run of `python -m sql.apply` succeeds and the two corrections are
  still there.
