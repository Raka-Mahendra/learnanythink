"""Settings: workspace management and local data."""

from __future__ import annotations

import streamlit as st

import db
import models
import state
from ui import layout as ui
from views import _common as common


def _workspace() -> None:
    st.subheader("Ruang belajar")
    workspace = state.workspace()
    if workspace is None:
        st.caption("Belum ada ruang belajar.")
        return

    with st.form("settings_workspace"):
        title = st.text_input("Nama", value=workspace.title, key="settings_ws_title")
        goal = st.text_area("Tujuan", value=workspace.goal, key="settings_ws_goal", height=90)
        level = st.selectbox(
            "Level",
            models.LEVELS,
            index=models.LEVELS.index(workspace.level) if workspace.level in models.LEVELS else 0,
            key="settings_ws_level",
        )
        saved = st.form_submit_button("Simpan ruang belajar", type="primary")
    if saved:
        if not goal.strip():
            st.error("Tujuan ruang belajar tidak boleh kosong.")
        else:
            db.update_workspace(
                workspace.id,
                title=title.strip() or workspace.title,
                goal=goal.strip(),
                level=level,
            )
            state.set_notice("Ruang belajar diperbarui.")
            st.rerun()

    stats = db.workspace_stats(workspace.id)
    st.caption(
        f"{stats.topics_total} topik · {stats.questions_total} soal · "
        f"{stats.topics_mastered} dikuasai"
    )


def _danger() -> None:
    st.subheader("Hapus data")
    workspace = state.workspace()
    with st.expander("Hapus ruang belajar ini"):
        st.warning("Topik, materi, chat, soal, dan riwayat latihan ikut terhapus.")
        if workspace is None:
            st.caption("Tidak ada ruang belajar aktif.")
        else:
            typed = st.text_input(
                f"Ketik {workspace.title} untuk konfirmasi",
                key="settings_delete_ws_confirm",
            )
            if st.button(
                "Hapus ruang belajar",
                key="settings_delete_ws",
                type="primary",
                disabled=typed.strip() != workspace.title,
            ):
                db.delete_workspace(workspace.id)
                state.clear_workspace()
                st.rerun()

    with st.expander("Hapus semua data"):
        typed = st.text_input("Ketik HAPUS untuk konfirmasi", key="settings_delete_all_confirm")
        if st.button(
            "Hapus semua data",
            key="settings_delete_all",
            type="primary",
            disabled=typed.strip() != "HAPUS",
        ):
            db.delete_all_data()
            state.clear_workspace()
            st.rerun()


def render() -> None:
    ui.header("settings")
    common.flash()
    _workspace()
    st.divider()
    _danger()