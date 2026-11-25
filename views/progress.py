"""Progress: mastery, scores, weak spots, and the learning journal."""

from __future__ import annotations

import streamlit as st

import db
import models
import state
from ui import layout as ui
from views import _common as common


def _chart_rows(workspace_id: str) -> list[dict]:
    return [
        {
            "Topik": f"{topic.position + 1}. {topic.title}",
            "Penguasaan": topic.mastery,
        }
        for topic in db.list_topics(workspace_id)
    ]


def render() -> None:
    ui.header("progress")
    common.flash()
    workspace = common.require_workspace()
    if workspace is None:
        return

    stats = db.workspace_stats(workspace.id)
    topics = db.list_topics(workspace.id)

    ui.metrics(
        [
            ("Penguasaan", f"{stats.mastery_percent}%", "Rata-rata penguasaan topik"),
            (
                "Rata-rata skor",
                f"{stats.average_score:.0f}" if stats.average_score is not None else "–",
                "Semua sesi latihan yang selesai",
            ),
            ("Rentetan hari", f"{stats.streak_days} hari", "Hari berturut-turut ada aktivitas"),
            ("Jatuh tempo", str(stats.due_reviews), "Soal yang perlu diulang hari ini"),
        ]
    )

    if not topics:
        ui.empty_state(
            "Belum ada yang bisa dipantau",
            "Susun peta belajar dan kerjakan latihan pertama.",
        )
        if st.button("Buka Peta Belajar", type="primary"):
            state.go("path")
        return

    st.divider()
    st.subheader("Penguasaan per topik")
    st.bar_chart(
        _chart_rows(workspace.id),
        x="Topik",
        y="Penguasaan",
        height=260,
    )

    weak = [topic for topic in topics if topic.mastery < 60]
    if weak:
        st.divider()
        st.subheader("Perlu perhatian")
        for topic in weak[:4]:
            with st.container(border=True):
                columns = st.columns([4, 1])
                with columns[0]:
                    st.markdown(f"**{topic.title}** · {topic.mastery}%")
                    if topic.summary:
                        st.caption(topic.summary)
                with columns[1]:
                    if st.button(
                        "Latih",
                        key=f"progress_train_{topic.id}",
                        width="stretch",
                    ):
                        common.prefill_practice(topic.id, "mc")

    mistakes = db.recent_mistakes(workspace.id, limit=5)
    if mistakes:
        st.divider()
        st.subheader("Kesalahan terakhir")
        for question in mistakes:
            with st.expander(question.text[:90]):
                if question.kind == "mc" and question.options:
                    st.write("Jawaban benar: " + question.options[question.answer])
                    if question.explanation:
                        st.caption(question.explanation)
                else:
                    if question.key_points:
                        for point in question.key_points:
                            st.markdown(f"- {point}")
                topic = db.get_topic(question.topic_id) if question.topic_id else None
                actions = st.columns(2)
                with actions[0]:
                    if topic and st.button(
                        "Materi",
                        key=f"progress_lesson_{question.id}",
                        width="stretch",
                    ):
                        state.select_topic(topic.id)
                        state.go("lesson")
                with actions[1]:
                    if st.button(
                        "Tutor",
                        key=f"progress_tutor_{question.id}",
                        width="stretch",
                    ):
                        if topic:
                            state.select_topic(topic.id)
                        state.set_notice("Tutor siap membahas soal ini.")
                        state.go("tutor")

    sessions = [session for session in db.list_sessions(workspace.id, limit=20) if session.finished]
    if sessions:
        st.divider()
        st.subheader("Riwayat latihan")
        history = []
        for session in sessions:
            topic = db.get_topic(session.topic_id) if session.topic_id else None
            history.append(
                {
                    "Tanggal": session.created_at[:10],
                    "Jenis": "Ulangan" if session.kind == "mixed" else models.KIND_LABELS.get(session.kind, session.kind),
                    "Topik": topic.title if topic else "Seluruh ruang belajar",
                    "Soal": len(session.question_ids),
                    "Skor": session.score,
                }
            )
        st.dataframe(history, hide_index=True, width="stretch")

    journal = db.list_journal(workspace.id, limit=5)
    if journal:
        st.divider()
        st.subheader("Jurnal")
        labels = {"milestone": "Pencapaian", "quiz": "Latihan", "note": "Catatan"}
        for entry in journal:
            label = labels.get(entry.kind, "Catatan")
            st.markdown(f"**{entry.created_at[:10]}** · {label} — {entry.content}")