"""Small native-Streamlit helpers. No custom CSS, no HTML fragments."""

from __future__ import annotations

from typing import Iterable, Optional

import streamlit as st

from models import STATUS_MASTERED, STATUS_LEARNING, STATUS_TODO, Topic
from pages import PAGE_BY_KEY

BADGE_COLORS = {
    STATUS_TODO: "gray",
    STATUS_LEARNING: "blue",
    STATUS_MASTERED: "green",
}


def header(page: str) -> None:
    """Page title prefixed with the same Material icon used in the sidebar."""
    entry = PAGE_BY_KEY.get(page)
    if entry is None:
        st.title(page)
        return
    st.title(f":material/{entry.icon}: {entry.title}")


def empty_state(title: str, body: str) -> None:
    with st.container(border=True):
        st.subheader(title)
        st.write(body)


def status_badge(topic: Topic) -> None:
    st.badge(topic.status_label, color=BADGE_COLORS.get(topic.status, "gray"))


def kind_badge(kind: str) -> None:
    label = {"mc": "Pilihan ganda", "essay": "Esai", "mixed": "Ulangan"}.get(kind, kind)
    color = {"mc": "blue", "essay": "violet", "mixed": "orange"}.get(kind, "gray")
    st.badge(label, color=color)


def metrics(items: Iterable[tuple[str, str, Optional[str]]]) -> None:
    items = list(items)
    columns = st.columns(len(items)) if items else []
    for column, (label, value, help_text) in zip(columns, items):
        with column:
            st.metric(label, value, help=help_text)