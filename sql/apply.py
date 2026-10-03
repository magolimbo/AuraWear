"""Create the enrichment tables and the clean views in BigQuery."""

from pathlib import Path

from google.cloud import bigquery

from config import CLEAN_DATASET, ENRICHMENT_DATASET, LOCATION, PROJECT_ID, RAW_DATASET

SQL_DIR = Path(__file__).parent

# Placeholders used in the SQL files, replaced with fully qualified dataset names.
PLACEHOLDERS = {
    "{raw}": f"{PROJECT_ID}.{RAW_DATASET}",
    "{clean}": f"{PROJECT_ID}.{CLEAN_DATASET}",
    "{enrichment}": f"{PROJECT_ID}.{ENRICHMENT_DATASET}",
}


def render(sql: str) -> str:
    """Replace the dataset placeholders in a SQL text."""
    for placeholder, dataset in PLACEHOLDERS.items():
        sql = sql.replace(placeholder, dataset)
    return sql


def main() -> None:
    """Run every .sql file in sql/ in name order, one query job each."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    for path in sorted(SQL_DIR.glob("*.sql")):
        client.query(render(path.read_text(encoding="utf-8"))).result()
        print(f"Applied {path.name}")


if __name__ == "__main__":
    main()
