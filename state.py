"""Streamlit session state and small navigation helpers.

Only UI state lives here. Everything durable is in ``db.py`` so a browser
refresh can rebuild the page from SQLite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import streamlit as st

import db
from models import Chat, QuizSession, Topic, Workspace

STATE_KEY = "la_state"


@dataclass
class Store:
    workspace_id: Optional[str] = None
    topic_id: Optional[str] = None
    chat_id: Optional[str] = None
    quiz_session_id: Optional[str] = None
    prefill: dict = field(default_factory=dict)
    notice: str = ""
    error: str = ""


def get() -> Store:
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = Store()
    return st.session_state[STATE_KEY]


def init() -> Store:
    store = get()
    workspaces = db.list_workspaces()
    ids = {workspace.id for workspace in workspaces}
    if store.workspace_id not in ids:
        store.workspace_id = workspaces[0].id if workspaces else None
        store.topic_id = None
        store.chat_id = None
        store.quiz_session_id = None
    return store


def workspace() -> Optional[Workspace]:
    store = get()
    if not store.workspace_id:
        return None
    return db.get_workspace(store.workspace_id)


def topics() -> list[Topic]:
    current = workspace()
    return db.list_topics(current.id) if current else []


def topic() -> Optional[Topic]:
    store = get()
    if not store.topic_id:
        return None
    current = db.get_topic(store.topic_id)
    if current is None or current.workspace_id != store.workspace_id:
        store.topic_id = None
        return None
    return current


def select_workspace(workspace_id: str) -> None:
    store = get()
    store.workspace_id = workspace_id
    store.topic_id = None
    store.chat_id = None
    store.quiz_session_id = None
    store.prefill = {}
    store.notice = ""
    store.error = ""


def clear_workspace() -> None:
    select_workspace("")


def select_topic(topic_id: Optional[str]) -> None:
    store = get()
    store.topic_id = topic_id
    store.quiz_session_id = None


def chat() -> Optional[Chat]:
    store = get()
    current = workspace()
    if current is None:
        return None
    if store.chat_id:
        found = db.get_chat(store.chat_id)
        if found and found.workspace_id == current.id:
            return found
    found = db.latest_chat(current.id)
    if found is None:
        found = db.create_chat(current.id)
    store.chat_id = found.id
    return found


def new_chat() -> Optional[Chat]:
    store = get()
    current = workspace()
    if current is None:
        return None
    found = db.create_chat(current.id, topic_id=store.topic_id)
    store.chat_id = found.id
    return found


def quiz_session() -> Optional[QuizSession]:
    store = get()
    if not store.quiz_session_id:
        return None
    session = db.get_session(store.quiz_session_id)
    if session is None or session.workspace_id != store.workspace_id:
        store.quiz_session_id = None
        return None
    return session


def select_quiz_session(session_id: Optional[str]) -> None:
    get().quiz_session_id = session_id


def set_notice(message: str) -> None:
    get().notice = message


def set_error(message: str) -> None:
    get().error = message


def clear_messages() -> None:
    store = get()
    store.notice = ""
    store.error = ""


def go(route: str) -> None:
    """Navigate to ``routes/<route>.py``; used after a successful action."""
    st.switch_page(f"routes/{route}.py")
