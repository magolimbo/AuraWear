"""Enrich feedback items with Gemini and append the results to BigQuery."""

from typing import Literal

from google import genai
from google.cloud import bigquery
from google.genai import types
from pydantic import BaseModel

from config import (
    CLEAN_DATASET,
    ENRICHMENT_DATASET,
    GEMINI_MODEL,
    LOCATION,
    PROJECT_ID,
    VERTEX_LOCATION,
)

FEEDBACK_TABLE = f"{PROJECT_ID}.{CLEAN_DATASET}.feedback"
ENRICHMENT_TABLE = f"{PROJECT_ID}.{ENRICHMENT_DATASET}.feedback_enrichment"

# Rules shared by every call (enrichment/SPEC.md section 3).
SYSTEM_INSTRUCTION = """\
You classify customer feedback for Aura Wear, a clothing brand.

Category: the cause of the issue, not the action the customer took.
- fit_sizing: size or fit
- product_quality: defects, materials
- returns_refunds: the return or refund process itself
- other: anything else
A return because of size is fit_sizing. If several issues are present, the main one decides.

Sentiment: the customer's (positive, neutral or negative). In a chat, ignore the agent's messages.

Summary (chat transcripts only): one sentence in English, using only facts from the text.
"""

# How each channel is described to the model, before the text.
CHANNELS = {
    "web_rating": "A product review comment",
    "support_chat": "A support chat transcript, one line per turn (Customer: / Agent:)",
}


class Tags(BaseModel):
    """LLM output for a rating comment."""

    category: Literal["fit_sizing", "product_quality", "returns_refunds", "other"]
    sentiment: Literal["positive", "neutral", "negative"]


class ChatTags(Tags):
    """LLM output for a chat transcript: the tags plus a one-sentence summary."""

    summary: str


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


def call_gemini(client: genai.Client, item: bigquery.Row) -> Tags:
    """Classify one item; raise if the call fails or the response does not match the schema."""
    schema = ChatTags if item["source_channel"] == "support_chat" else Tags
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{CHANNELS[item['source_channel']]}:\n{item['text']}",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0,
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    return schema.model_validate_json(response.text)


def insert_row(client: bigquery.Client, item: bigquery.Row, tags: Tags) -> None:
    """Append one enrichment row; raise if BigQuery rejects it."""
    row = {
        "feedback_id": item["feedback_id"],
        "category": tags.category,
        "sentiment": tags.sentiment,
        "summary": tags.summary if isinstance(tags, ChatTags) else None,
    }
    errors = client.insert_rows_json(ENRICHMENT_TABLE, [row])
    if errors:
        raise RuntimeError(f"Insert failed for {item['feedback_id']}: {errors}")


def main() -> None:
    bq = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    gemini = genai.Client(vertexai=True, project=PROJECT_ID, location=VERTEX_LOCATION)

    items = select_items(bq)
    enriched = failed = 0
    for item in items:
        try:
            tags = call_gemini(gemini, item)
        except Exception as error:
            # Nothing is written: the item is selected again on the next run.
            print(f"Failed {item['feedback_id']}: {error}")
            failed += 1
            continue
        insert_row(bq, item, tags)
        enriched += 1

    print(f"Selected {len(items)}, enriched {enriched}, failed {failed}")


if __name__ == "__main__":
    main()
