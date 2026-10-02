"""Upload the generated files to Cloud Storage and load them into BigQuery raw tables."""

from pathlib import Path

from google.cloud import bigquery, storage

from config import BUCKET, LOCATION, PROJECT_ID, RAW_DATASET

DATA_DIR = Path("data")

# Columns of each raw table, from SPEC.md section 4.1.
SOURCES = {
    "web_rating": ["review_id", "order_id", "product_id", "stars", "comment", "created_at"],
    "support_chat": ["chat_id", "order_id", "transcript", "started_at"],
    "orders": ["order_id", "order_date", "customer_id", "product_id", "product_name", "returned"],
}


def upload_files(client: storage.Client) -> None:
    """Upload every file in data/ to gs://<bucket>/<source>/<file>, unchanged.

    Simulates the source systems delivering their daily files.
    """
    bucket = client.bucket(BUCKET)
    for path in sorted(DATA_DIR.glob("*/*")):
        name = path.relative_to(DATA_DIR).as_posix()
        bucket.blob(name).upload_from_filename(str(path))
        print(f"Uploaded gs://{BUCKET}/{name}")


def load_tables(client: bigquery.Client) -> None:
    """Replace each raw table with all files of its source in the bucket."""
    for source, columns in SOURCES.items():
        job_config = bigquery.LoadJobConfig(
            schema=[bigquery.SchemaField(column, "STRING") for column in columns],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        if source == "orders":
            job_config.source_format = bigquery.SourceFormat.CSV
            job_config.skip_leading_rows = 1
        else:
            job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON

        table_id = f"{PROJECT_ID}.{RAW_DATASET}.{source}"
        uri = f"gs://{BUCKET}/{source}/*"
        client.load_table_from_uri(uri, table_id, job_config=job_config).result()
        print(f"Loaded {client.get_table(table_id).num_rows} rows into {table_id}")


def main() -> None:
    upload_files(storage.Client(project=PROJECT_ID))
    load_tables(bigquery.Client(project=PROJECT_ID, location=LOCATION))


if __name__ == "__main__":
    main()
