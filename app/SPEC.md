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
