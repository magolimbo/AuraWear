# AuraWear

Prototype of an Intelligent Customer Feedback Workbench on GCP: synthetic
feedback and orders are loaded into BigQuery, enriched with Gemini (category,
sentiment, one-sentence summary for chats) and explored in a Streamlit app where
a product manager can correct the AI tags.

![Architecture](docs/architecture.svg)

## Components

| Folder | What it does | GCP services |
|---|---|---|
| `data_gen/` | Generates daily files: web ratings, support chats, orders | — |
| `ingestion/` | Uploads the files to Cloud Storage and loads them into `raw` tables | Cloud Storage, BigQuery |
| `sql/` | Creates the `clean` views and the empty `enrichment` tables | BigQuery |
| `enrichment/` | Sends each feedback text to Gemini and stores the structured output | Vertex AI, BigQuery |
| `app/` | Workbench: search, filter, compare text with AI output, correct a tag | BigQuery |

Shared contracts are in [SPEC.md](SPEC.md); each folder has its own `SPEC.md`.
Project id, bucket, datasets and regions are in [config.py](config.py).

## Setup

Requires Python 3.11+ and a GCP project with the bucket and the `raw`, `clean`
and `enrichment` datasets (names in `config.py`) and the Vertex AI API enabled.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
gcloud auth application-default login
```

Authentication uses Application Default Credentials; no key files.

## Run

```powershell
python -m data_gen.generate                  # 1. local files in data/
python -m ingestion.load                     # 2. Cloud Storage and raw tables
python -m sql.apply                          # 3. views and tables (first time, or when the SQL changes)
python -m enrichment.enrich                  # 4. Gemini enrichment, only items not yet enriched
python -m streamlit run app/workbench.py     # 5. workbench in the browser
```

Every step is safe to re-run. Lint with `ruff check .`.
