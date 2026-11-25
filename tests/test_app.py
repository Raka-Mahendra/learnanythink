"""End-to-end demo flow through Streamlit's AppTest harness (no network calls)."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

import db

ROOT = Path(__file__).resolve().parents[1]


def _button(at: AppTest, label: str):
    matches = [button for button in at.button if button.label == label]
    assert matches, f"tombol {label!r} tidak ditemukan"
    return matches[0]


def test_demo_learning_loop(temp_db):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
    at.run()
    assert not at.exception

    demo = [button for button in at.button if button.key == "home_demo"]
    assert demo, "tombol contoh demo harus tersedia saat mode demo"
    demo[0].click().run()
    assert not at.exception

    workspaces = db.list_workspaces()
    assert len(workspaces) == 1
    workspace = workspaces[0]
    topics = db.list_topics(workspace.id)
    assert len(topics) == 5

    at.switch_page("routes/path.py").run()
    assert not at.exception

    at.switch_page("routes/lesson.py").run()
    assert not at.exception
    _button(at, "Tulis materi").click().run()
    assert not at.exception
    lesson = db.latest_lesson(topics[0].id)
    assert lesson is not None
    assert lesson.body["sections"]

    _button(at, "Tandai selesai").click().run()
    assert not at.exception
    assert db.latest_lesson(topics[0].id).completed is True

    at.selectbox(key="lesson_topic_pick").set_value(f"2. {topics[1].title}").run()
    assert not at.exception
    _button(at, "Tulis materi").click().run()
    assert not at.exception
    assert db.latest_lesson(topics[1].id) is not None
    _button(at, "← Topik sebelumnya").click().run()
    assert not at.exception
    assert at.selectbox(key="lesson_topic_pick").value == f"1. {topics[0].title}"

    at.switch_page("routes/practice.py").run()
    assert not at.exception
    _button(at, "Buat soal").click().run()
    assert not at.exception

    sessions = [session for session in db.list_sessions(workspace.id) if not session.finished]
    assert sessions, "sesi latihan harus dibuat"
    session = sessions[0]
    questions = db.questions_by_ids(session.question_ids)
    assert len(questions) == 5

    for question in questions:
        at.radio(key=f"practice_mc_{question.id}").set_value(question.answer)
    at.run()

    _button(at, "Kumpulkan jawaban").click().run()
    assert not at.exception
    finished = db.get_session(session.id)
    assert finished.finished_at
    assert finished.score == 100
    assert db.count_questions(workspace.id) >= 5

    _button(at, "Latihan baru").click().run()
    assert not at.exception
    at.radio(key="practice_kind").set_value("Esai")
    at.run()
    _button(at, "Buat soal").click().run()
    assert not at.exception

    essay_sessions = [
        item for item in db.list_sessions(workspace.id) if not item.finished and item.kind == "essay"
    ]
    assert essay_sessions, "sesi esai harus dibuat"
    essay_session = essay_sessions[0]
    essay_questions = db.questions_by_ids(essay_session.question_ids)
    answer = (
        "Alam semesta tidak dimulai dari singularitas. Fase sebelumnya menyusut, lalu "
        "berbalik mengembang pada kepadatan ekstrem, sehingga Big Bang adalah titik "
        "pantulan dan bukan awal mutlak dari ketiadaan."
    )
    for question in essay_questions:
        at.text_area(key=f"practice_essay_{question.id}").set_value(answer)
    at.run()
    _button(at, "Kumpulkan jawaban").click().run()
    assert not at.exception
    graded = db.get_session(essay_session.id)
    assert graded.finished_at
    assert graded.score and graded.score > 0

    at.switch_page("routes/bank.py").run()
    assert not at.exception

    due_question = db.list_questions(workspace.id, kind="mc")[0]
    db.upsert_review(due_question.id, "2000-01-01", 1, 2.5, 1, 0)
    at.run()
    _button(at, "Mulai ulangan").click().run()
    assert not at.exception
    review_sessions = [
        item for item in db.list_sessions(workspace.id) if not item.finished and item.kind == "mixed"
    ]
    assert review_sessions, "sesi ulangan harus dibuat dari soal yang jatuh tempo"
    review = review_sessions[0]
    review_question = db.questions_by_ids(review.question_ids)[0]
    at.switch_page("routes/practice.py").run()
    assert not at.exception
    at.radio(key=f"practice_mc_{review_question.id}").set_value(review_question.answer)
    at.run()
    _button(at, "Kumpulkan jawaban").click().run()
    assert not at.exception
    assert db.get_session(review.id).finished_at

    at.switch_page("routes/progress.py").run()
    assert not at.exception
    assert db.get_topic(topics[0].id).mastery > 0

    chat = db.create_chat(workspace.id, title="Uji tutor")
    db.add_message(chat.id, "user", "Halo tutor")
    db.add_message(chat.id, "assistant", "Halo juga")
    at.switch_page("routes/tutor.py").run()
    assert not at.exception
    assert any("Halo tutor" in item.value for item in at.markdown)

    at.switch_page("routes/settings.py").run()
    assert not at.exception