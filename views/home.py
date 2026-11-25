"""Home: start a workspace or continue the active one."""

from __future__ import annotations

import streamlit as st

import db
import state
from models import LEVELS, STATUS_MASTERED
from services import demo, quiz
from ui import layout as ui
from views import _common as common


def _new_workspace_form(key: str) -> None:
    with st.form(f"{key}_form"):
        goal = st.text_area(
            "Apa yang ingin kamu kuasai?",
            key=f"{key}_goal",
            placeholder="Contoh: dasar fotografi dengan ponsel",
            height=90,
        )
        level = st.selectbox("Level", LEVELS, key=f"{key}_level")
        submitted = st.form_submit_button("Mulai belajar", type="primary")
    if submitted:
        common.create_workspace("", goal, level)


def render() -> None:
    ui.header("home")
    common.flash()

    workspaces = db.list_workspaces()
    if not workspaces:
        st.subheader("Mulai dari satu tujuan")
        _new_workspace_form("home_new")
        if demo_label_available():
            if st.button(f"Coba contoh: {demo.SAMPLE_TITLE}", key="home_demo"):
                common.create_workspace(demo.SAMPLE_TITLE, demo.SAMPLE_GOAL, "pemula")
        return

    store = state.get()
    if store.workspace_id is None:
        store.workspace_id = workspaces[0].id
    open_new = bool(store.prefill.pop("open_new", False))
    current = state.workspace() or workspaces[0]
    stats = db.workspace_stats(current.id)
    topics = db.list_topics(current.id)

    if open_new:
        st.subheader("Ruang belajar baru")
        _new_workspace_form("home_new_open")
        st.divider()

    ui.metrics(
        [
            (
                "Topik dikuasai",
                f"{stats.topics_mastered}/{stats.topics_total}",
                "Topik berstatus Paham",
            ),
            (
                "Rata-rata skor",
                f"{stats.average_score:.0f}" if stats.average_score is not None else "–",
                "Dari sesi latihan yang selesai",
            ),
            ("Jatuh tempo", str(stats.due_reviews), "Soal yang perlu diulang hari ini"),
        ]
    )

    st.divider()
    st.subheader(current.title)
    st.caption(f"{current.goal} · level {current.level}")
    st.progress(stats.mastery_percent / 100, text=f"Penguasaan {stats.mastery_percent}%")

    active_topic = next(
        (topic for topic in topics if topic.status != STATUS_MASTERED),
        topics[0] if topics else None,
    )
    if active_topic is not None:
        if st.button("Lanjut belajar", type="primary", width="stretch", key="home_continue"):
            state.select_topic(active_topic.id)
            state.go("lesson")

    nav = st.columns(2)
    with nav[0]:
        if st.button("Peta belajar", width="stretch", key="home_go_path"):
            state.go("path")
    with nav[1]:
        if st.button(
            "Latihan",
            width="stretch",
            key="home_go_practice",
            disabled=active_topic is None,
        ):
            common.prefill_practice(active_topic.id if active_topic else None, "mc")

    if stats.due_reviews:
        st.warning(f"{stats.due_reviews} soal siap diulang.")
        if st.button("Mulai ulangan", key="home_start_review"):
            session = quiz.create_review_session(current)
            if session:
                state.select_quiz_session(session.id)
                state.go("practice")

    if active_topic:
        with st.container(border=True):
            st.markdown(f"**Fokus: {active_topic.title}**")
            if active_topic.summary:
                st.caption(active_topic.summary)

    if len(workspaces) > 1:
        st.divider()
        st.subheader("Ruang belajar lain")
        for workspace in workspaces:
            if workspace.id == current.id:
                continue
            with st.container(border=True):
                columns = st.columns([4, 1])
                with columns[0]:
                    st.markdown(f"**{workspace.title}**")
                with columns[1]:
                    if st.button("Buka", key=f"home_open_{workspace.id}", width="stretch"):
                        state.select_workspace(workspace.id)
                        st.rerun()

    with st.expander("Ruang belajar baru"):
        _new_workspace_form("home_more")


def demo_label_available() -> bool:
    from services import llm

    return llm.offline()