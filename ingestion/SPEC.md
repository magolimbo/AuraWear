# ingestion — SPEC

Loads the generated files into BigQuery `raw` tables through Cloud Storage
(`SPEC.md` §4.1). Uses names from `config.py`.

## 1. Interface

`python -m ingestion.load`

Two steps, run in order:

1. `upload_files`: uploads every file in `data/` to `gs://<bucket>/<source>/<file>`,
   unchanged, overwriting existing objects. Simulates the source systems
   delivering their daily files.
2. `load_tables`: one load job per source from `gs://<bucket>/<source>/*` into
   `raw.<source>`, replacing the table content:
   - explicit schema from `SPEC.md` §4.1, all columns STRING (no autodetect);
   - JSON as newline-delimited; CSV skips the header row;
   - a missing `comment` becomes NULL.

Any failure stops the run with the error.

**Prerequisite:** bucket and datasets exist (created once by hand, `SPEC.md` §3).
**Dependencies:** `google-cloud-storage`, `google-cloud-bigquery`.

## 2. Verified by

Run it after `python -m data_gen.generate`, then check:

- Row counts of the three raw tables equal the line counts of their files
  (CSV minus the header), dirty rows included.
- A second run leaves the same counts (content replaced, not appended).
