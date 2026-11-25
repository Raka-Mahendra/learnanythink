"""Learning path: inspect, edit, and rebuild the topic map."""

from __future__ import annotations

import streamlit as st

import db
import state
from ui import layout as ui
from views import _common as common


def _objectives(raw: str) -> list[str]:
    return [line.strip(" -•\t") for line in raw.splitlines() if line.strip(" -•\t")]


def _topic_card(topic, total: int) -> None:
    with st.container(border=True):
        top = st.columns([5, 1])
        with top[0]:
            st.markdown(f"**{topic.position + 1}. {topic.title}**")
            if topic.summary:
                st.caption(topic.summary)
        with top[1]:
            ui.status_badge(topic)
        st.progress(
            topic.mastery / 100,
            text=f"Penguasaan {topic.mastery}%",
        )

        actions = st.columns(3)
        with actions[0]:
            if st.button("Materi", key=f"path_lesson_{topic.id}", width="stretch"):
                state.select_topic(topic.id)
                state.go("lesson")
        with actions[1]:
            if st.button("Latihan", key=f"path_quiz_{topic.id}", width="stretch"):
                common.prefill_practice(topic.id, "mc")
        with actions[2]:
            with st.popover("Kelola", width="stretch"):
                with st.form(f"path_edit_{topic.id}"):
                    title = st.text_input("Judul", value=topic.title, key=f"path_title_{topic.id}")
                    summary = st.text_area(
                        "Ringkasan", value=topic.summary, key=f"path_sum_{topic.id}", height=80
                    )
                    objectives = st.text_area(
                        "Poin tujuan (satu per baris)",
                        value="\n".join(topic.objectives),
                        key=f"path_obj_{topic.id}",
                        height=110,
                    )
                    saved = st.form_submit_button("Simpan perubahan")
                if saved:
                    db.update_topic(
                        topic.id,
                        title=title.strip() or topic.title,
                        summary=summary.strip(),
                        objectives=_objectives(objectives),
                    )
                    st.rerun()

                move = st.columns(2)
                with move[0]:
                    if st.button(
                        "Naikkan",
                        key=f"path_up_{topic.id}",
                        disabled=topic.position == 0,
                        width="stretch",
                    ):
                        db.move_topic(topic.id, -1)
                        st.rerun()
                with move[1]:
                    if st.button(
                        "Turunkan",
                        key=f"path_down_{topic.id}",
                        disabled=topic.position >= total - 1,
                        width="stretch",
                    ):
                        db.move_topic(topic.id, 1)
                        st.rerun()

                st.divider()
                confirm = st.checkbox(
                    "Saya yakin ingin menghapus topik ini",
                    key=f"path_del_confirm_{topic.id}",
                )
                if st.button(
                    "Hapus topik",
                    key=f"path_del_{topic.id}",
                    type="primary",
                    disabled=not confirm,
                ):
                    db.delete_topic(topic.id)
                    if state.get().topic_id == topic.id:
                        state.select_topic(None)
                    st.rerun()


def render() -> None:
    ui.header("path")
    common.flash()
    workspace = common.require_workspace()
    if workspace is None:
        return

    topics = db.list_topics(workspace.id)
    stats = db.workspace_stats(workspace.id)
    st.progress(
        stats.mastery_percent / 100,
        text=f"{stats.topics_mastered} dari {stats.topics_total} topik dikuasai",
    )

    if not topics:
        ui.empty_state(
            "Belum ada topik",
            "Susun peta dari tujuan ruang belajar ini.",
        )
        if st.button("Susun peta belajar", type="primary", key="path_build_empty"):
            common.rebuild_path(workspace)
    else:
        with st.expander("Susun ulang peta"):
            st.warning(
                "Topik dan materinya akan diganti. Bank soal tetap tersimpan."
            )
            confirm = st.checkbox("Saya mengerti", key="path_rebuild_confirm")
            if st.button(
                "Susun ulang sekarang",
                key="path_rebuild",
                type="primary",
                disabled=not confirm,
            ):
                common.rebuild_path(workspace)

    for topic in topics:
        _topic_card(topic, len(topics))

    st.divider()
    with st.expander("Tambah topik manual"):
        with st.form("path_add"):
            title = st.text_input("Judul topik", key="path_add_title")
            summary = st.text_area("Ringkasan", key="path_add_summary", height=80)
            objectives = st.text_area(
                "Poin tujuan (satu per baris)", key="path_add_objectives", height=100
            )
            submitted = st.form_submit_button("Tambah topik")
        if submitted:
            if not title.strip():
                st.error("Judul topik wajib diisi.")
            else:
                db.create_topic(
                    workspace.id,
                    title,
                    summary,
                    _objectives(objectives),
                )
                state.set_notice("Topik baru ditambahkan.")
                st.rerun()
