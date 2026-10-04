# app — SPEC

The feedback workbench: a single-screen Streamlit app to search, filter and
open feedback items, compare the original text with the AI output, and correct
a tag (`SPEC.md` G4). Uses names from `config.py`.

## 1. Interface

`python -m streamlit run app/workbench.py`

Reads `clean.feedback_workbench`; writes only `enrichment.feedback_corrections`
(`SPEC.md` §3).

**Layout** (wide page):

| Zone | Content |
|---|---|
| Sidebar | Filters (§2) |
| Main, top | Title, search box, results table (§2) |
| Main, bottom | Detail of the selected row: original text and AI output side by side, correction form (§3, §4) |

**Data loading.**
- When the app starts, one query reads every row of
  `clean.feedback_workbench`. The result is cached, and search and filters run
  in Python on that cached data.
- After a correction is saved, the cache is cleared and the data is reloaded.

**Theme.** Colors and font are set in `.streamlit/config.toml`, with no custom
CSS:
- warm off-white background, charcoal text;
- one accent color, used for buttons and the selected row.

- Labels are shown in plain words: `fit_sizing` becomes "Fit & sizing",
  `support_chat` becomes "Support chat". Stored values never change.
- If a BigQuery call fails, the error is shown in the page.

**Prerequisite:** SQL applied (`SPEC.md` §3).
**Dependencies:** `google-cloud-bigquery`, `streamlit`, `db-dtypes`.

## 2. List, search and filters

**Search.** One text box, case-insensitive: it keeps the items whose `text`
contains the typed text as one phrase (e.g. "too small" matches only those two
words together). When it is empty, it filters nothing.

**Filters** (sidebar). Filters and search combine: an item is shown only if it
passes all of them.

| Filter | Options |
|---|---|
| Date | Range from–to on the date of `created_at`; default: first to last date in the data |
| Channel | Web rating, Support chat |
| Returned | Returned, Not returned |
| Category | The four categories (`SPEC.md` §4.3) |
| Sentiment | positive, neutral, negative |
| Product | Product names in the data, alphabetical |

- Date is a date-range picker; all the other filters are multiselects.
- An empty multiselect filters nothing. The date range applies only once both
  dates are chosen.
- Items without text have no category or sentiment, so they never match the
  category or sentiment filters, nor the search.

**Results.**
- Above the table: "N of M feedback items", where M is the total.
- Rows are ordered newest first.

| Column | From |
|---|---|
| Date | `created_at`, date only |
| Channel | `source_channel` |
| Product | `product_name` |
| Stars | `stars` as ★★☆☆☆, empty for chats |
| Category, Sentiment | `category`, `sentiment` (current values, after corrections) |
| Returned | `returned` |
| Corrected | `is_corrected` |
| Text | start of `text`, cut to the column width; the full text is in the detail (§3) |

**Selection.**
- Clicking a row selects it (one row at a time) and opens its detail (§3).
- Changing the search or a filter clears the selection, so the detail never
  shows an item that is no longer in the list.

## 3. Detail

Shown below the table when a row is selected. Otherwise the area shows:
"Select a feedback item in the table to see its detail."

**Header:** the product name as title. Below it, in small text: channel ·
date and time · order · customer · Returned / Not returned, then the
`feedback_id`.

**Two bordered cards of equal width:**

| Left: Original text | Right: AI analysis |
|---|---|
| **Chat:** the transcript as chat messages, one per line, with one icon for `Customer:` and one for `Agent:` (prefix removed) | Category and sentiment as badges next to their names: sentiment green / gray / red, always with the word; category in blue, a color the sentiment does not use |
| **Rating with comment:** stars (★★☆☆☆), then the comment | **Chats only:** the summary |
| **Rating without comment:** stars, then "No written comment" | Below: the correction form (§4) |

- **Corrected field:** a field whose current value differs from the AI value
  (`category` ≠ `ai_category`, the same for sentiment) shows "Corrected" next
  to the badge and, below in small text, "AI: <AI value>".
- **No AI output** (`ai_category` NULL): the right column shows only a message,
  and no form.
  - No text: "Not analyzed: no text to send to the AI."
  - Text present: "Not analyzed yet." This happens when the item was loaded but
    the enrichment has not run yet, or its call failed (`enrichment` §4).

## 4. Correction

**Form**, in the right column of the detail, only for items with AI output
(`ai_category` not NULL):
- Category: select with the four categories, prefilled with the current
  `category`.
- Sentiment: select with the three values, prefilled with the current
  `sentiment`.
- Button "Save correction", disabled until at least one select differs from
  the current value.

Options are shown with plain labels (§1) and saved as stored values
(`fit_sizing`), so only allowed values can be written.

**Save.** Only the fields whose selected value differs from the current one are
appended to `enrichment.feedback_corrections`, with one INSERT statement, one
row per changed field:

| Column | Value |
|---|---|
| `feedback_id` | the item's |
| `field` | `category` or `sentiment` |
| `corrected_value` | the selected value |
| `corrected_at` | `CURRENT_TIMESTAMP()`, set by BigQuery |

- `feedback_id` and the values are passed as query parameters, never written
  into the SQL text.
- One statement for both fields: either both rows are saved or neither is.

**After the save.**
- The app shows the message "Correction saved", clears the cache and reloads
  the data (§1).
- The detail stays on the same item and shows the new value with "Corrected".
- If the new value no longer matches the active filters (for example, the list
  is filtered on Product quality and the category becomes Fit & sizing), the
  item leaves the list and the detail closes, as in §2.
- If the INSERT fails, the error is shown and nothing is reloaded.

## 5. Verified by

Start the app with `python -m streamlit run app/workbench.py`, then check:

1. **Start.** The page opens with no error. M in "N of M feedback items"
   equals the row count of `clean.feedback_workbench`.
2. **Search and filters.** For each case, N equals the count of the same
   condition in SQL on `clean.feedback_workbench`:
   - one word in the search (e.g. "small");
   - each filter alone, including a one-day date range;
   - one combination: Product = Wool Sweater, Category = Product quality,
     Returned = Returned.
3. **Selection.** Select a row, then change a filter: the detail goes back to
   the hint message.
4. **Detail.** Open one item of each kind:
   - a chat: messages, summary and badges;
   - a rating with comment: stars and comment, no summary;
   - a rating without comment: stars, "No written comment",
     "Not analyzed: no text to send to the AI." and no form.
5. **Correction.**
   - The button is disabled until a select changes.
   - Change only the category and save:
     - the detail shows the new value, "Corrected" and "AI: <old value>";
     - the table shows Corrected for that row;
     - `feedback_corrections` has exactly one new row for that item.
   - Change both fields and save: two new rows with the same `corrected_at`.
   - `ai_category` and `ai_sentiment` of the item are unchanged.
6. **Leaving the filter.** With Category = Product quality active, correct an
   item to Fit & sizing: the item leaves the list and the detail closes.
7. **Restart.** Stop and restart the app: the corrections are still shown.
