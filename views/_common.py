"""Shared flows for the page modules: workspace, path, lessons, prefill."""

from __future__ import annotations

from typing import Optional

import streamlit as st

import db
import state
from models import Lesson, Topic, Workspace
from services import learning, llm
from ui import layout as ui


def flash() -> None:
    """Show a queued success/error message once, then clear it."""
    store = state.get()
    if store.error:
        st.error(store.error)
        store.error = ""
    if store.notice:
        st.success(store.notice)
        store.notice = ""


def title_from_goal(goal: str) -> str:
    clean = " ".join(goal.split()).strip(" .?!")
    if not clean:
        return "Ruang belajar baru"
    words = clean.split()[:6]
    title = " ".join(words)
    return title[:50].strip().capitalize()


def require_workspace() -> Optional[Workspace]:
    workspace = state.workspace()
    if workspace is None:
        ui.empty_state(
            "Belum ada ruang belajar",
            "Buat ruang belajar pertama di Beranda.",
        )
        if st.button("Buka Beranda", type="primary"):
            state.go("home")
        return None
    return workspace


def require_topics(workspace: Workspace) -> list[Topic]:
    topics = db.list_topics(workspace.id)
    if not topics:
        ui.empty_state(
            "Peta belajar belum ada",
            "Susun peta topik dulu.",
        )
        if st.button("Buka Peta Belajar", type="primary"):
            state.go("path")
    return topics


def create_workspace(title: str, goal: str, level: str) -> None:
    goal = goal.strip()
    if not goal:
        st.error("Tuliskan dulu apa yang ingin kamu kuasai.")
        return
    workspace = db.create_workspace(
        title=title.strip() or title_from_goal(goal),
        goal=goal,
        level=level,
    )
    state.select_workspace(workspace.id)
    try:
        with st.status("Menyusun peta belajar...", expanded=False) as status:
            items = learning.generate_path(workspace)
            topics = learning.apply_path(workspace.id, items)
            db.add_journal(
                workspace.id,
                "milestone",
                f"Peta belajar disusun: {len(topics)} topik untuk tujuan \"{workspace.goal}\".",
            )
            status.update(label=f"{len(topics)} topik siap", state="complete")
        state.set_notice("Ruang belajar siap.")
    except llm.LLMError as exc:
        state.set_error(
            "Ruang belajar dibuat, tetapi peta belajar belum tersusun. " + str(exc)
        )
    st.rerun()


def rebuild_path(workspace: Workspace) -> None:
    try:
        with st.status("Menyusun ulang peta belajar...", expanded=False) as status:
            items = learning.generate_path(workspace)
            topics = learning.apply_path(workspace.id, items)
            status.update(label=f"{len(topics)} topik siap", state="complete")
        state.set_notice("Peta belajar diperbarui.")
    except llm.LLMError as exc:
        state.set_error(str(exc))
    st.rerun()


def generate_lesson(workspace: Workspace, topic: Topic) -> Optional[Lesson]:
    try:
        with st.status("Menulis materi...", expanded=False) as status:
            body, model = learning.generate_lesson(workspace, topic)
            lesson = learning.save_lesson(topic.id, body, model)
            status.update(label="Materi siap", state="complete")
        state.set_notice(f"Materi \"{topic.title}\" sudah ditulis.")
        return lesson
    except llm.LLMError as exc:
        state.set_error(str(exc))
        return None


def prefill_practice(topic_id: Optional[str], kind: str, count: int = 5) -> None:
    state.get().prefill = {
        "topic_id": topic_id,
        "kind": kind,
        "count": count,
    }
    state.go("practice")