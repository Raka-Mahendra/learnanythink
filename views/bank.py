"""Question bank: browse, filter, and manage saved questions."""

from __future__ import annotations

import streamlit as st

import db
import models
import state
from services import quiz
from ui import layout as ui
from views import _common as common


def _kind_choice() -> tuple[str, str]:
    label = st.selectbox("Jenis", ["Semua jenis", "Pilihan ganda", "Esai"], key="bank_kind")
    return label, {"Pilihan ganda": "mc", "Esai": "essay"}.get(label, "")


def _question_block(question: models.Question) -> None:
    meta = db.get_review(question.id)
    with st.expander(question.text[:90] + ("..." if len(question.text) > 90 else "")):
        ui.kind_badge(question.kind)
        st.write(question.text)
        if question.kind == "mc":
            for index, option in enumerate(question.options):
                prefix = "**Benar:** " if index == question.answer else ""
                st.markdown(f"{quiz.option_letter(index)}. {prefix}{option}")
            if question.explanation:
                st.caption(question.explanation)
        else:
            if question.key_points:
                st.markdown("**Poin kunci**")
                for point in question.key_points:
                    st.markdown(f"- {point}")
            if question.model_answer:
                st.markdown("**Jawaban acuan**")
                st.write(question.model_answer)

        columns = st.columns([2, 2, 1])
        with columns[0]:
            topic = db.get_topic(question.topic_id) if question.topic_id else None
            st.caption(f"Topik: {topic.title if topic else 'tanpa topik'}")
        with columns[1]:
            if meta:
                st.caption(f"Ulangan berikutnya: {meta.due_at} · {meta.reps} kali diulang")
            else:
                st.caption("Belum masuk jadwal ulangan")
        with columns[2]:
            with st.popover("Hapus", width="stretch"):
                st.write("Hapus soal ini dari bank?")
                confirm = st.checkbox("Ya, hapus", key=f"bank_confirm_{question.id}")
                if st.button(
                    "Hapus soal",
                    key=f"bank_delete_{question.id}",
                    type="primary",
                    disabled=not confirm,
                ):
                    db.delete_question(question.id)
                    st.rerun()


def render() -> None:
    ui.header("bank")
    common.flash()
    workspace = common.require_workspace()
    if workspace is None:
        return

    topics = db.list_topics(workspace.id)
    topic_labels = ["Semua topik"] + [f"{topic.position + 1}. {topic.title}" for topic in topics]
    topic_map = {f"{topic.position + 1}. {topic.title}": topic for topic in topics}

    filters = st.columns([2, 1, 2])
    with filters[0]:
        topic_label = st.selectbox("Topik", topic_labels, key="bank_topic")
    with filters[1]:
        kind_label, kind = _kind_choice()
    with filters[2]:
        search = st.text_input("Cari soal", key="bank_search", placeholder="kata kunci")

    topic = topic_map.get(topic_label)
    questions = db.list_questions(
        workspace.id,
        topic_id=topic.id if topic else None,
        kind=kind or None,
        search=search,
    )
    total = db.count_questions(workspace.id)
    st.caption(f"{len(questions)} dari {total} soal")

    if not questions:
        ui.empty_state(
            "Belum ada soal yang cocok",
            "Buat latihan dulu; soal otomatis tersimpan di sini.",
        )
        if st.button("Buat latihan", type="primary"):
            common.prefill_practice(topic.id if topic else None, "mc")
        return

    bulk = st.columns(2)
    with bulk[0]:
        if st.button(
            "Latih",
            key="bank_practice_topic",
            width="stretch",
            disabled=topic is None,
        ):
            common.prefill_practice(topic.id if topic else None, "mc")
    with bulk[1]:
        if st.button("Mulai ulangan", key="bank_review", width="stretch"):
            if db.count_due(workspace.id) == 0:
                st.info("Belum ada soal yang jatuh tempo hari ini.")
            else:
                session = quiz.create_review_session(workspace)
                if session:
                    state.select_quiz_session(session.id)
                    state.go("practice")

    for question in questions:
        _question_block(question)