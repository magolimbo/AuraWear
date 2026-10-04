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


@st.cache_data(show_spinner="Loading feedback...")
def load_feedback() -> pd.DataFrame:
    """Read every row of the workbench view; cached until a correction is saved."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    return client.query(f"SELECT * FROM `{WORKBENCH_VIEW}`").to_dataframe()


st.set_page_config(page_title="Feedback Workbench", layout="wide")

feedback = load_feedback()

st.sidebar.header("Filters")

st.title("Feedback Workbench")
st.caption(f"{len(feedback)} feedback items")
