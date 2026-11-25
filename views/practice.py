"""Practice: create a quiz, answer it, and read the graded result."""

from __future__ import annotations

import streamlit as st

import db
import models
import state
from models import Question, QuizSession, Workspace
from services import llm, quiz
from ui import layout as ui
from views import _common as common

KIND_OPTIONS = {"Pilihan ganda": "mc", "Esai": "essay"}
COUNT_RANGE = (3, 10)


def _label(session: QuizSession) -> str:
    if session.kind == "mixed":
        return "Ulangan terjadwal"
    return models.KIND_LABELS.get(session.kind, "Latihan")


def _status_label(attempt, question: Question) -> str:
    if attempt is None:
        return "Belum dijawab"
    if question.kind == "essay" and attempt.points is not None:
        if attempt.points >= 70:
            return "Benar"
        if attempt.points >= 50:
            return "Sebagian benar"
        return "Perlu diperbaiki"
    return "Benar" if getattr(attempt, "is_correct", False) else "Salah"


def _apply_prefill(workspace: Workspace) -> None:
    store = state.get()
    if not store.prefill:
        return
    prefill = store.prefill
    store.prefill = {}
    topics = db.list_topics(workspace.id)
    if prefill.get("topic_id"):
        for topic in topics:
            if topic.id == prefill["topic_id"]:
                st.session_state["practice_topic"] = f"{topic.position + 1}. {topic.title}"
                break
    kind = prefill.get("kind")
    if kind in KIND_OPTIONS.values():
        st.session_state["practice_kind"] = next(
            label for label, value in KIND_OPTIONS.items() if value == kind
        )
    if prefill.get("count"):
        st.session_state["practice_count"] = max(
            COUNT_RANGE[0], min(COUNT_RANGE[1], int(prefill["count"]))
        )


def _setup(workspace: Workspace) -> None:
    _apply_prefill(workspace)
    topics = db.list_topics(workspace.id)
    labels = ["Seluruh ruang belajar"] + [
        f"{topic.position + 1}. {topic.title}" for topic in topics
    ]
    by_label = {f"{topic.position + 1}. {topic.title}": topic for topic in topics}

    with st.container(border=True):
        st.subheader("Buat latihan")
        topic_label = st.selectbox("Topik", labels, key="practice_topic")
        columns = st.columns(2)
        with columns[0]:
            kind_label = st.radio(
                "Jenis soal",
                list(KIND_OPTIONS),
                horizontal=True,
                key="practice_kind",
            )
        with columns[1]:
            difficulty = st.selectbox(
                "Kesulitan",
                quiz.DIFFICULTIES,
                index=1,
                key="practice_difficulty",
            )
        count = st.slider(
            "Jumlah soal",
            COUNT_RANGE[0],
            COUNT_RANGE[1],
            5,
            key="practice_count",
        )
        start = st.button("Buat soal", type="primary", key="practice_start")

    if start:
        topic = by_label.get(topic_label)
        try:
            with st.status("Menyiapkan soal...", expanded=False) as status:
                session = quiz.create_quiz(
                    workspace,
                    topic,
                    KIND_OPTIONS[kind_label],
                    count,
                    difficulty,
                )
                status.update(label=f"{len(session.question_ids)} soal siap", state="complete")
        except llm.LLMError as exc:
            st.error(str(exc))
            return
        state.select_quiz_session(session.id)
        if topic:
            state.select_topic(topic.id)
        st.rerun()

    recent = [session for session in db.list_sessions(workspace.id, limit=3) if session.finished]
    if recent:
        st.divider()
        st.subheader("Sesi terakhir")
        for session in recent:
            topic = db.get_topic(session.topic_id) if session.topic_id else None
            with st.container(border=True):
                columns = st.columns([4, 1])
                with columns[0]:
                    st.markdown(f"**{_label(session)}**")
                    st.caption(
                        f"{topic.title if topic else 'Seluruh ruang belajar'} · "
                        f"{session.created_at[:10]} · skor {session.score}/100"
                    )
                with columns[1]:
                    if st.button(
                        "Lihat hasil",
                        key=f"practice_open_{session.id}",
                        width="stretch",
                    ):
                        state.select_quiz_session(session.id)
                        st.rerun()


def _render_question_head(index: int, total: int, question: Question) -> None:
    st.markdown(f"**Soal {index + 1} dari {total}**")
    st.write(question.text)
    if question.kind == "essay":
        st.caption("2–4 kalimat, sertakan alasan.")


def _run_session(session: QuizSession) -> None:
    questions = db.questions_by_ids(session.question_ids)
    attempts = quiz.attempts_map(session.id)
    pending = [question for question in questions if question.id not in attempts]
    done = len(questions) - len(pending)

    st.caption(
        f"{_label(session)} · {done} dari {len(questions)} soal terjawab"
    )
    st.progress(done / max(1, len(questions)))

    if pending:
        with st.form(f"practice_form_{session.id}"):
            answers: dict[str, object] = {}
            for index, question in enumerate(questions):
                if question.id in attempts:
                    continue
                st.divider()
                _render_question_head(index, len(questions), question)
                if question.kind == "mc":
                    answers[question.id] = st.radio(
                        "Pilih satu jawaban",
                        options=list(range(len(question.options))),
                        format_func=lambda value, q=question: quiz.answer_label(q, value),
                        index=None,
                        key=f"practice_mc_{question.id}",
                        label_visibility="collapsed",
                    )
                else:
                    answers[question.id] = st.text_area(
                        "Jawabanmu",
                        key=f"practice_essay_{question.id}",
                        height=120,
                        label_visibility="collapsed",
                    )
            submitted = st.form_submit_button("Kumpulkan jawaban", type="primary")

        if submitted:
            essay_answers: dict[str, str] = {}
            answered = 0
            for question in pending:
                value = answers.get(question.id)
                if question.kind == "mc":
                    if isinstance(value, int):
                        quiz.answer_mc(session, question, value)
                        answered += 1
                else:
                    text = str(value or "").strip()
                    if text:
                        essay_answers[question.id] = text
                        answered += 1
            if essay_answers:
                try:
                    with st.status("Menilai jawaban esai...", expanded=False) as status:
                        quiz.grade_essays(
                            session,
                            essay_answers,
                            question_ids=list(essay_answers),
                        )
                        status.update(label="Jawaban dinilai", state="complete")
                except llm.LLMError as exc:
                    st.error(str(exc))
                    return
            final = quiz.finish_if_ready(session)
            if final is not None:
                state.set_notice(f"Latihan selesai dengan skor {final}/100.")
                st.rerun()
            if answered:
                st.rerun()
            st.warning("Masih ada soal yang belum dijawab.")

    if done:
        st.divider()
        st.subheader("Sudah dijawab")
        for index, question in enumerate(questions):
            attempt = attempts.get(question.id)
            if attempt is None:
                continue
            status = _status_label(attempt, question)
            with st.expander(f"{status} · Soal {index + 1}: {question.text[:70]}"):
                if question.kind == "mc":
                    choice = attempt.answer_text if isinstance(attempt.answer_text, str) else ""
                    if choice.isdigit():
                        st.write("Jawabanmu: " + quiz.answer_label(question, int(choice)))
                    st.write("Jawaban benar: " + quiz.answer_label(question, question.answer))
                    if question.explanation:
                        st.caption(question.explanation)
                else:
                    st.write("Jawabanmu:")
                    st.write(attempt.answer_text or "(kosong)")
                    if attempt.feedback:
                        st.info(attempt.feedback)
                    if question.model_answer:
                        st.write("Jawaban acuan:")
                        st.write(question.model_answer)


def _results(session: QuizSession) -> None:
    questions = db.questions_by_ids(session.question_ids)
    attempts = quiz.attempts_map(session.id)
    score = session.score or 0
    correct = sum(1 for item in attempts.values() if getattr(item, "is_correct", False))

    ui.metrics(
        [
            ("Skor", f"{score}/100", "Skor sesi ini"),
            ("Benar", f"{correct}/{len(questions)}", "Jumlah jawaban tepat"),
            ("Jenis", _label(session), "Jenis sesi"),
        ]
    )
    if score >= 80:
        st.success("Sudah kuat. Lanjut ke topik berikutnya.")
    elif score >= 60:
        st.info("Cukup. Ulangi bagian yang masih lemah.")
    else:
        st.warning("Perlu diulang. Baca materi lalu coba lagi.")

    st.divider()
    for index, question in enumerate(questions):
        attempt = attempts.get(question.id)
        status = _status_label(attempt, question)
        with st.expander(
            f"{status} · Soal {index + 1}: {question.text[:70]}",
            expanded=status in {"Salah", "Perlu diperbaiki"},
        ):
            st.write(question.text)
            if question.kind == "mc":
                if attempt and str(attempt.answer_text).isdigit():
                    st.write("Jawabanmu: " + quiz.answer_label(question, int(attempt.answer_text)))
                else:
                    st.write("Jawabanmu: tidak dijawab")
                st.write("Jawaban benar: " + quiz.answer_label(question, question.answer))
                if question.explanation:
                    st.caption(question.explanation)
            else:
                st.write("Jawabanmu:")
                st.write(attempt.answer_text if attempt and attempt.answer_text else "(kosong)")
                if attempt and attempt.points is not None:
                    st.caption(f"Nilai: {attempt.points}/100")
                if attempt and attempt.feedback:
                    st.info(attempt.feedback)
                if question.key_points:
                    st.write("Poin kunci:")
                    for point in question.key_points:
                        st.markdown(f"- {point}")
                if question.model_answer:
                    st.write("Jawaban acuan:")
                    st.write(question.model_answer)

    due = db.get_review(questions[0].id) if questions else None
    if due and due.due_at:
        st.caption(f"Diulang mulai {due.due_at}.")

    st.divider()
    columns = st.columns(3)
    with columns[0]:
        if questions and st.button("Latihan baru", width="stretch", key="practice_again"):
            first = questions[0]
            state.select_quiz_session(None)
            common.prefill_practice(first.topic_id, session.kind if session.kind != "mixed" else "mc")
    with columns[1]:
        if st.button("Buka bank soal", width="stretch", key="practice_to_bank"):
            state.select_quiz_session(None)
            state.go("bank")
    with columns[2]:
        if st.button("Selesai", width="stretch", key="practice_done"):
            state.select_quiz_session(None)
            state.go("home")


def render() -> None:
    ui.header("practice")
    common.flash()
    workspace = common.require_workspace()
    if workspace is None:
        return
    topics = db.list_topics(workspace.id)
    if not topics:
        ui.empty_state(
            "Belum ada topik",
            "Susun peta belajar dulu.",
        )
        if st.button("Buka Peta Belajar", type="primary"):
            state.go("path")
        return

    session = state.quiz_session()
    if session is not None and session.finished and state.get().prefill:
        state.select_quiz_session(None)
        session = None
    if session is None:
        _setup(workspace)
    elif session.finished:
        _results(session)
    else:
        _run_session(session)