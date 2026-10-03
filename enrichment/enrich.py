"""Enrich feedback items with Gemini and append the results to BigQuery."""

from google.cloud import bigquery

from config import CLEAN_DATASET, ENRICHMENT_DATASET, LOCATION, PROJECT_ID

FEEDBACK_TABLE = f"{PROJECT_ID}.{CLEAN_DATASET}.feedback"
ENRICHMENT_TABLE = f"{PROJECT_ID}.{ENRICHMENT_DATASET}.feedback_enrichment"


def select_items(client: bigquery.Client) -> list[bigquery.Row]:
    """Return the feedback items that have text and no enrichment row yet."""
    query = f"""
        SELECT feedback_id, source_channel, text
        FROM `{FEEDBACK_TABLE}` AS f
        WHERE f.text IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM `{ENRICHMENT_TABLE}` AS e WHERE e.feedback_id = f.feedback_id
          )
    """
    return list(client.query(query).result())


def main() -> None:
    items = select_items(bigquery.Client(project=PROJECT_ID, location=LOCATION))
    print(f"Selected {len(items)} items")


if __name__ == "__main__":
    main()
