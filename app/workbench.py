"""Feedback workbench: search, filter and open feedback items, and correct AI tags."""

import pandas as pd
import streamlit as st
from google.cloud import bigquery

from config import CLEAN_DATASET, ENRICHMENT_DATASET, LOCATION, PROJECT_ID

WORKBENCH_VIEW = f"{PROJECT_ID}.{CLEAN_DATASET}.feedback_workbench"
CORRECTIONS_TABLE = f"{PROJECT_ID}.{ENRICHMENT_DATASET}.feedback_corrections"

# One statement for both tags, so either both rows are saved or neither is.
# An unchanged tag is passed as NULL and skipped.
INSERT_CORRECTIONS = f"""
    INSERT INTO `{CORRECTIONS_TABLE}` (feedback_id, field, corrected_value, corrected_at)
    SELECT @feedback_id, field, value, CURRENT_TIMESTAMP()
    FROM UNNEST([
      STRUCT('category' AS field, @category AS value),
      STRUCT('sentiment', @sentiment)
    ])
    WHERE value IS NOT NULL
"""

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
SENTIMENT_COLORS = {"positive": "green", "neutral": "gray", "negative": "red"}


@st.cache_data(show_spinner="Loading feedback...")
def load_feedback() -> pd.DataFrame:
    """Read every row of the workbench view; cached until a correction is saved."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    return client.query(f"SELECT * FROM `{WORKBENCH_VIEW}`").to_dataframe()


def stars_text(stars: float) -> str:
    """Show a 1-5 rating as filled and empty stars, e.g. 2 -> ★★☆☆☆."""
    count = int(stars)  # pandas passes 2.0, not 2, when the column has empty values
    return "★" * count + "☆" * (5 - count)


def show_original_text(item: pd.Series) -> None:
    """Left column of the detail: a chat as messages, a rating as stars and comment."""
    if item["source_channel"] == "support_chat":
        for line in item["text"].splitlines():
            speaker, _, message = line.partition(": ")  # "Customer: ..." or "Agent: ..."
            avatar = ":material/person:" if speaker == "Customer" else ":material/support_agent:"
            with st.chat_message(speaker, avatar=avatar):
                st.caption(speaker)
                st.text(message)
    else:
        st.subheader(stars_text(item["stars"]), anchor=False)
        if pd.isna(item["text"]):
            st.caption("No written comment")
        else:
            st.text(item["text"])


def show_tag(name: str, value: str, ai_value: str, color: str) -> None:
    """Show one tag as a badge next to its name; if a person changed it, also the AI value."""
    corrected = value != ai_value
    line = f"**{name}** :{color}-badge[{LABELS[value]}]"
    if corrected:
        line += " :gray[:material/edit: Corrected]"
    st.markdown(line)
    if corrected:
        st.caption(f"AI: {LABELS[ai_value]}")


def show_ai_analysis(item: pd.Series) -> None:
    """Right column of the detail: tags and summary, or why there are none."""
    if pd.isna(item["ai_category"]):
        if pd.isna(item["text"]):
            st.caption("Not analyzed: no text to send to the AI.")
        else:
            st.caption("Not analyzed yet.")
        return
    # Blue for the category: green, gray and red mean sentiment only.
    show_tag("Category", item["category"], item["ai_category"], "blue")
    sentiment_color = SENTIMENT_COLORS[item["sentiment"]]
    show_tag("Sentiment", item["sentiment"], item["ai_sentiment"], sentiment_color)
    if pd.notna(item["summary"]):
        st.markdown("**Summary**")
        st.text(item["summary"])


def save_correction(feedback_id: str, category: str | None, sentiment: str | None) -> None:
    """Append the changed tags (None = unchanged) to feedback_corrections, then reload."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("feedback_id", "STRING", feedback_id),
            bigquery.ScalarQueryParameter("category", "STRING", category),
            bigquery.ScalarQueryParameter("sentiment", "STRING", sentiment),
        ]
    )
    client.query(INSERT_CORRECTIONS, job_config=job_config).result()
    load_feedback.clear()  # reached only if the insert succeeded
    st.toast("Correction saved", icon=":material/check:")


def show_correction_form(item: pd.Series) -> None:
    """Two selects starting from the current tags; Save is enabled only after a change."""
    st.markdown("**Correct tags**")
    # Keys include the item id, so each item's selects start from its own tags.
    category_col, sentiment_col = st.columns(2)
    category = category_col.selectbox(
        "Category",
        CATEGORIES,
        index=CATEGORIES.index(item["category"]),
        format_func=LABELS.get,
        key=f"category:{item['feedback_id']}",
    )
    sentiment = sentiment_col.selectbox(
        "Sentiment",
        SENTIMENTS,
        index=SENTIMENTS.index(item["sentiment"]),
        format_func=LABELS.get,
        key=f"sentiment:{item['feedback_id']}",
    )
    new_category = category if category != item["category"] else None
    new_sentiment = sentiment if sentiment != item["sentiment"] else None
    # The save runs as a callback, before the next run, so that run already reads fresh data.
    st.button(
        "Save correction",
        type="primary",
        disabled=new_category is None and new_sentiment is None,
        on_click=save_correction,
        args=(item["feedback_id"], new_category, new_sentiment),
    )


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
    st.stop()

# Detail of the selected item (app/SPEC.md section 3).
item = shown.iloc[event.selection.rows[0]]
st.divider()
returned_text = "Returned" if item["returned"] else "Not returned"
st.subheader(item["product_name"], anchor=False)
st.caption(
    f"{LABELS[item['source_channel']]} · {item['created_at']:%Y-%m-%d %H:%M} UTC · "
    f"Order {item['order_id']} · Customer {item['customer_id']} · {returned_text}  \n"
    f"{item['feedback_id']}"
)

# Two bordered cards side by side; the correction form sits in the AI card.
left, right = st.columns(2, gap="large")
with left.container(border=True):
    st.markdown("**Original text**")
    show_original_text(item)
with right.container(border=True):
    st.markdown("**AI analysis**")
    show_ai_analysis(item)
    if pd.notna(item["ai_category"]):  # only AI output can be corrected
        st.divider()
        show_correction_form(item)
