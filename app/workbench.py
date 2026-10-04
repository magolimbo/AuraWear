"""Feedback workbench: search, filter and open feedback items, and correct AI tags."""

import pandas as pd
import streamlit as st
from google.cloud import bigquery

from config import CLEAN_DATASET, LOCATION, PROJECT_ID

WORKBENCH_VIEW = f"{PROJECT_ID}.{CLEAN_DATASET}.feedback_workbench"

# Plain labels shown in the interface; stored values never change (app/SPEC.md section 1).
LABELS = {
    "web_rating": "Web rating",
    "support_chat": "Support chat",
    "fit_sizing": "Fit & sizing",
    "product_quality": "Product quality",
    "returns_refunds": "Returns & refunds",
    "other": "Other",
    "positive": "Positive",
    "neutral": "Neutral",
    "negative": "Negative",
}
CATEGORIES = ["fit_sizing", "product_quality", "returns_refunds", "other"]
SENTIMENTS = ["positive", "neutral", "negative"]


@st.cache_data(show_spinner="Loading feedback...")
def load_feedback() -> pd.DataFrame:
    """Read every row of the workbench view; cached until a correction is saved."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    return client.query(f"SELECT * FROM `{WORKBENCH_VIEW}`").to_dataframe()


def stars_text(stars: float) -> str:
    """Show a 1-5 rating as filled and empty stars, e.g. 2 -> ★★☆☆☆."""
    count = int(stars)  # pandas passes 2.0, not 2, when the column has empty values
    return "★" * count + "☆" * (5 - count)


st.set_page_config(page_title="Feedback Workbench", layout="wide")

feedback = load_feedback()

# Sidebar filters (app/SPEC.md section 2). An empty multiselect filters nothing.
st.sidebar.header("Filters")
dates = feedback["created_at"].dt.date
date_range = st.sidebar.date_input("Date", value=(dates.min(), dates.max()))
channels = st.sidebar.multiselect("Channel", ["web_rating", "support_chat"], format_func=LABELS.get)
returned = st.sidebar.multiselect(
    "Returned", [True, False], format_func=lambda value: "Returned" if value else "Not returned"
)
categories = st.sidebar.multiselect("Category", CATEGORIES, format_func=LABELS.get)
sentiments = st.sidebar.multiselect("Sentiment", SENTIMENTS, format_func=LABELS.get)
products = st.sidebar.multiselect("Product", sorted(feedback["product_name"].unique()))

st.title("Feedback Workbench")
search = st.text_input("Search feedback text", placeholder='e.g. "too small"')

# Apply search and filters; an item is shown only if it passes all of them.
shown = feedback
if search:
    shown = shown[shown["text"].str.contains(search, case=False, regex=False, na=False)]
if len(date_range) == 2:  # the range applies only once both dates are chosen
    start, end = date_range
    shown = shown[shown["created_at"].dt.date.between(start, end)]
for column, selected in [
    ("source_channel", channels),
    ("returned", returned),
    ("category", categories),
    ("sentiment", sentiments),
    ("product_name", products),
]:
    if selected:
        shown = shown[shown[column].isin(selected)]
shown = shown.sort_values(["created_at", "feedback_id"], ascending=False)

st.caption(f"{len(shown)} of {len(feedback)} feedback items")

table = pd.DataFrame(
    {
        "Date": shown["created_at"].dt.date,
        "Channel": shown["source_channel"].map(LABELS),
        "Product": shown["product_name"],
        "Stars": shown["stars"].map(stars_text, na_action="ignore").fillna(""),
        "Category": shown["category"].map(LABELS).fillna(""),
        "Sentiment": shown["sentiment"].map(LABELS).fillna(""),
        "Returned": shown["returned"],
        "Corrected": shown["is_corrected"],
        "Text": shown["text"].fillna(""),
    }
)

# Streamlit remembers the selected row by position. The key changes whenever the
# list of shown items changes, which clears the selection, so a position never
# points to a different item.
event = st.dataframe(
    table,
    hide_index=True,
    height=350,
    column_config={"Text": st.column_config.TextColumn(width="large")},
    on_select="rerun",
    selection_mode="single-row",
    key=str(hash(tuple(shown["feedback_id"]))),
)

if not event.selection.rows:
    st.info("Select a feedback item in the table to see its detail.", icon=":material/touch_app:")
