# enrichment — SPEC

Enriches feedback items with Gemini on Vertex AI and appends the results to
`enrichment.feedback_enrichment` (`SPEC.md` §4.3). Uses names from `config.py`.

## 1. Interface

`python -m enrichment.enrich`

Three steps:

1. Select the items to enrich (§2).
2. For each item, one at a time, call Gemini (§3).
3. Right after each successful call, insert its row into
   `enrichment.feedback_enrichment` (§4).

At the end it prints the number of items selected, enriched and failed.

**Configuration.** Two new constants in `config.py`:

| Constant | Value | Why |
|---|---|---|
| `VERTEX_LOCATION` | `europe-west1` | Vertex needs a region; `LOCATION = "EU"` is a BigQuery multi-region |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Available in EU regions; enough for 4 categories and a one-sentence summary |

The Gemini client is `google-genai` with `vertexai=True`, project and region
from `config.py`. Authentication is via Application Default Credentials; no
API key.

- Safe to re-run: an item that already has a row is never sent again.
- A failed Gemini call does not stop the run (§4). Any other failure (the
  selection query, the insert into BigQuery) stops the run with the error.

**Prerequisite:** SQL applied (`SPEC.md` §3), Vertex AI API enabled.
**Dependencies:** `google-cloud-bigquery`, `google-genai`, `pydantic`.

## 2. Item selection

One query on `clean.feedback`, keeping the items that:

- have `text` (`text IS NOT NULL`): ratings without a comment are never
  enriched;
- have no row in `enrichment.feedback_enrichment` (`NOT EXISTS` on
  `feedback_id`).

Columns read: `feedback_id`, `source_channel`, `text`.

Because `clean.feedback` always holds every item ever loaded, this rule alone
decides what to enrich:

- **First run:** all items with text.
- **Following runs:** the new items, plus the ones whose call failed on an
  earlier run.

`clean.feedback` has one row per `feedback_id`, so each item is selected at
most once per run.

## 3. Prompt and structured output

One call per item, with temperature 0 so the output is as repeatable as
possible (Gemini does not guarantee identical answers).

**Output schema** (Pydantic model, passed to Gemini as the response schema),
chosen by `source_channel`:

| Model | Fields | Used for |
|---|---|---|
| `Tags` | `category` (one of `fit_sizing`, `product_quality`, `returns_refunds`, `other`), `sentiment` (one of `positive`, `neutral`, `negative`) | `web_rating` |
| `ChatTags` | the fields of `Tags`, plus `summary` (string) | `support_chat` |

**System instruction** (the same for every call) contains:

- the four categories with their definitions from `SPEC.md` §4.3, and the
  rule "classify the cause, not the action" with its example;
- if several issues are present, the main one decides the category;
- sentiment is the customer's: in a chat, the agent's messages do not count;
- summary (chats only): one sentence in English, only facts from the text.

**User message:** the channel, described in words ("a product review comment"
or "a support chat transcript, one line per turn, `Customer:` / `Agent:`"),
followed by `text`.

A call counts as failed (§4) if it raises an error or if its response does not
match the schema.

## 4. Write and errors

**Successful call.** One row is inserted right away into
`enrichment.feedback_enrichment` with a streaming insert (`insert_rows_json`):

| Column | Value |
|---|---|
| `feedback_id` | the item's |
| `category`, `sentiment` | from the response |
| `summary` | from the response for chats; NULL for ratings |

The row is queryable at once, so the workbench shows it without waiting for the
end of the run. If the insert returns errors, the run stops (§1).

**Failed call** (error, or response not matching the schema):

- it prints `feedback_id` and the error, and moves on to the next item;
- nothing is written and there is no retry in the run: the item is selected
  again on the next run (§2).

**Interrupted run** (crash, Ctrl+C): rows already written stay; the next run
enriches only the missing items.

Only responses validated by the schema are written, so the table holds only
allowed values.

## 5. Verified by

Run in this order:

1. **Forced failure.** Temporarily set `GEMINI_MODEL` to a model that does not
   exist and run `python -m enrichment.enrich`.
   - Every call fails and the error is printed for each item.
   - The run reaches the end; failed = selected.
   - `enrichment.feedback_enrichment` is still empty.
   - Then restore `GEMINI_MODEL`.
2. **First run.** Run it again.
   - Selected = items with `text` in `clean.feedback`; enriched + failed =
     selected.
   - Rows in `enrichment.feedback_enrichment` = enriched, and each
     `feedback_id` appears once.
   - `category` and `sentiment` hold only allowed values (`SPEC.md` §4.3).
   - `summary` is non-NULL in every chat row and NULL in every rating row.
3. **Second run,** right after: it selects only the items that failed in the
   first run (normally 0) and adds no duplicates.
4. **Workbench view.** In `clean.feedback_workbench`, every item with text has
   `ai_category`, except the ones that failed; the two test corrections still
   apply.
5. **Spot check.** Read about 10 items, both channels and every category, and
   compare the text with category, sentiment and summary.
