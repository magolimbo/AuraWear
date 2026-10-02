# data_gen — SPEC

Generates synthetic daily source files in the format of `SPEC.md` §4.1, so the
pipeline can run end to end without real data.

## 1. Interface

`python -m data_gen.generate [--days 3] [--orders-per-day 200] [--start-date 2026-09-01] [--seed 42]`

- Writes `data/<source>/<YYYY-MM-DD>.<ext>` for each day and source
  (`web_rating`, `support_chat`, `orders`); `data/` is git-ignored.
- Same arguments, same files (deterministic given the seed).
- Overwrites existing files for the generated days.
- Formats: orders CSV with header; all JSON values are strings; dates
  `YYYY-MM-DD`; timestamps ISO 8601 UTC.
- Random choices are uniform unless stated otherwise.

## 2. Orders

- Catalogue: 12 fixed products in code (`P01`–`P12`, clothing names).
  Two are "problem products": `P03` runs small, `P07` has a quality defect.
- Customers: pool of 300 (`C0001`–`C0300`).
- `order_id` = `O<YYYYMMDD>-<NNNN>`, unique across days; `order_date` = file day.
- `returned` = `true` / `false`: 10% for normal products, 35% for problem products.

## 3. Feedback

**Which orders get feedback** (independently):
- Rating: 80% of orders; 50% of ratings have a comment (otherwise `comment` is omitted).
- Chat: 50% of returned orders, 10% of the others.
- `review_id` = `R<order_id>`, `chat_id` = `CH<order_id>`.
- Feedback is in the file of its order's day, at a random time of that day.

**Category and sentiment**, chosen for every rating and chat:

| Case | Rating | Chat |
|---|---|---|
| Product `P03` (runs small) | negative, `fit_sizing` | negative, `fit_sizing` |
| Product `P07` (defect) | negative, `product_quality` | negative, `product_quality` |
| Other product, returned | negative; `fit_sizing`, `product_quality` or `returns_refunds` | negative; `fit_sizing`, `product_quality` or `returns_refunds` |
| Other product, not returned | 80% positive, 20% neutral; `fit_sizing`, `product_quality` or `other` | negative; `fit_sizing` or `product_quality` |

- Category and sentiment only choose stars and text; they are not written to the files.
- Stars follow sentiment: negative 1–2, neutral 3, positive 4–5.
- Texts come from templates in code, with a `{product}` placeholder for the product name:
  - rating comments: at least 5 per (category, sentiment) pair in the table;
  - chat openings (first customer turn, carries the complaint): at least 5 per category in the table;
  - follow-up turns: generic customer and agent lines.
- A chat transcript has 4–6 turns, starting with `Customer:` and alternating with `Agent:`, one per line.

## 4. Dirty rows

Each day, about 2% of feedback rows are dirty, with at least one of each type:

| Type | How |
|---|---|
| Duplicate | an existing rating or chat line written twice |
| Stars out of range | an existing rating with `stars` = `0` or `6` |

The orders file is always clean.

## 5. Verified by

`pytest tests/data_gen` (files written to a temporary directory), default arguments:

- Files are named as in §1; CSV header and JSON keys match `SPEC.md` §4.1
  (`comment` may be absent).
- Two runs with the same arguments produce identical files.
- Every rating and chat references an order of the same day.
- Each day has at least one duplicate and one out-of-range row.
