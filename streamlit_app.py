"""LearnAnythink — router, page config, and the sidebar workspace picker."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

import db
import state
from pages import PAGES
from services import llm

ROOT = Path(__file__).resolve().parent
LOGO = ROOT / "Logo Kit" / "png" / "lockup-horizontal-dark-transparent.png"
SYMBOL = ROOT / "Logo Kit" / "png" / "symbol-color.png"
ICON = ROOT / "Logo Kit" / "icons" / "favicon.ico"

st.set_page_config(
    page_title="LearnAnythink",
    page_icon=str(SYMBOL) if SYMBOL.exists() else (str(ICON) if ICON.exists() else None),
    layout="centered",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def _prepare() -> bool:
    db.init()
    return True


_prepare()

if LOGO.exists():
    st.logo(str(LOGO), icon_image=str(SYMBOL) if SYMBOL.exists() else None, size="large")


def _on_workspace_change() -> None:
    state.select_workspace(st.session_state.get("sidebar_workspace", ""))


def _sidebar() -> None:
    store = state.init()
    workspaces = db.list_workspaces()
    with st.sidebar:
        if workspaces:
            ids = [workspace.id for workspace in workspaces]
            by_id = {workspace.id: workspace for workspace in workspaces}
            current = store.workspace_id if store.workspace_id in ids else ids[0]
            if st.session_state.get("sidebar_workspace") != current:
                st.session_state["sidebar_workspace"] = current
            st.selectbox(
                "Ruang belajar",
                ids,
                format_func=lambda value: by_id[value].title,
                key="sidebar_workspace",
                on_change=_on_workspace_change,
            )
            workspace = by_id.get(store.workspace_id or current)
            if workspace:
                due = db.count_due(workspace.id)
                caption = f"Level {workspace.level} · {db.count_questions(workspace.id)} soal"
                if due:
                    caption += f" · {due} jatuh tempo"
                st.caption(caption)
            if st.button("Ruang belajar baru", width="stretch", key="sidebar_new"):
                state.get().prefill = {"open_new": True}
                state.go("home")
        else:
            st.caption("Belum ada ruang belajar.")

        if llm.offline():
            st.caption("Mode contoh")


page = st.navigation(
    [
        st.Page(item.path, title=item.title, icon=f":material/{item.icon}:", url_path=item.key)
        for item in PAGES
    ],
    position="sidebar",
)

_sidebar()
page.run()
