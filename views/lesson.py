"""Lesson page: read generated material and hand off to practice."""

from __future__ import annotations

import streamlit as st

import db
import state
from services import learning
from ui import layout as ui
from views import _common as common


def _render_body(body: dict) -> None:
    if body.get("objective"):
        st.info(body["objective"])
    for section in body.get("sections", []):
        st.subheader(section.get("heading", ""))
        st.write(section.get("body", ""))
    if body.get("key_terms"):
        st.subheader("Istilah kunci")
        st.dataframe(
            [
                {"Istilah": term.get("term", ""), "Arti": term.get("definition", "")}
                for term in body["key_terms"]
            ],
            hide_index=True,
            width="stretch",
        )
    if body.get("example"):
        with st.container(border=True):
            st.markdown("**Contoh**")
            st.write(body["example"])
    if body.get("recap"):
        st.success(body["recap"])


def render() -> None:
    ui.header("lesson")
    common.flash()
    workspace = common.require_workspace()
    if workspace is None:
        return
    topics = common.require_topics(workspace)
    if not topics:
        return

    store = state.get()
    default_index = 0
    for index, topic in enumerate(topics):
        if topic.id == store.topic_id:
            default_index = index
            break
    labels = [f"{topic.position + 1}. {topic.title}" for topic in topics]
    sync = st.session_state.pop("lesson_topic_sync", None)
    if sync in labels:
        st.session_state["lesson_topic_pick"] = sync
    if st.session_state.get("lesson_topic_pick") not in labels:
        st.session_state["lesson_topic_pick"] = labels[default_index]
    choice = st.selectbox("Topik", labels, key="lesson_topic_pick")
    topic = topics[labels.index(choice)]
    if store.topic_id != topic.id:
        state.select_topic(topic.id)

    head = st.columns([4, 1])
    with head[0]:
        st.subheader(topic.title)
    with head[1]:
        ui.status_badge(topic)

    lesson = db.latest_lesson(topic.id)
    if lesson is None:
        ui.empty_state(
            "Materi belum ditulis",
            "Materi dibuat dari tujuan topik ini.",
        )
        if st.button("Tulis materi", type="primary", key="lesson_generate_empty"):
            common.generate_lesson(workspace, topic)
            st.rerun()
        return

    _render_body(lesson.body)

    st.divider()
    if lesson.completed:
        st.success("Materi selesai.")
    else:
        if st.button("Tandai selesai", type="primary", key="lesson_complete"):
            learning.mark_lesson_complete(lesson, topic)
            state.set_notice("Materi selesai. Penguasaan diperbarui.")
            st.rerun()

    actions = st.columns(2)
    with actions[0]:
        if st.button(
            "Kuis pilihan ganda",
            key="lesson_to_mc",
            width="stretch",
        ):
            common.prefill_practice(topic.id, "mc")
    with actions[1]:
        if st.button("Kuis esai", key="lesson_to_essay", width="stretch"):
            common.prefill_practice(topic.id, "essay")

    with st.expander("Tulis ulang materi"):
        st.write("Materi lama akan diganti.")
        confirm = st.checkbox("Saya ingin menulis ulang", key="lesson_rewrite_confirm")
        if st.button(
            "Tulis ulang",
            key="lesson_rewrite",
            disabled=not confirm,
        ):
            common.generate_lesson(workspace, topic)
            st.rerun()

    st.divider()
    nav = st.columns(2)
    with nav[0]:
        if st.button(
            "← Topik sebelumnya",
            key="lesson_prev",
            disabled=topic.position == 0,
            width="stretch",
        ):
            target = topics[topic.position - 1]
            state.select_topic(target.id)
            st.session_state["lesson_topic_sync"] = f"{target.position + 1}. {target.title}"
            st.rerun()
    with nav[1]:
        if st.button(
            "Topik berikutnya →",
            key="lesson_next",
            disabled=topic.position >= len(topics) - 1,
            width="stretch",
        ):
            target = topics[topic.position + 1]
            state.select_topic(target.id)
            st.session_state["lesson_topic_sync"] = f"{target.position + 1}. {target.title}"
            st.rerun()
