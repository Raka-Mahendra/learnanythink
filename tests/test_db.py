from __future__ import annotations

import db
from models import STATUS_LEARNING, STATUS_TODO
from services import learning, quiz


def test_workspace_and_topics_roundtrip(temp_db):
    workspace = db.create_workspace("Kosmologi", "Memahami Big Bounce")
    topics = db.replace_topics(
        workspace.id,
        [
            {"title": "Dasar", "summary": "Ringkas", "objectives": ["A", "B"]},
            {"title": "Bukti", "summary": "", "objectives": []},
        ],
    )
    assert [topic.title for topic in topics] == ["Dasar", "Bukti"]
    assert topics[0].objectives == ["A", "B"]
    assert topics[0].status == STATUS_TODO
    db.move_topic(topics[1].id, -1)
    assert db.list_topics(workspace.id)[0].title == "Bukti"


def test_lesson_completion_updates_mastery(temp_db):
    workspace = db.create_workspace("Topik", "Tujuan")
    topic = db.replace_topics(
        workspace.id, [{"title": "Satu", "summary": "", "objectives": []}]
    )[0]
    lesson = db.save_lesson(topic.id, {"title": "Materi"})
    assert db.latest_lesson(topic.id).completed is False
    db.complete_lesson(lesson.id)
    learning.refresh_topic(topic.id)
    updated = db.get_topic(topic.id)
    assert updated.mastery == 20
    assert updated.status == STATUS_LEARNING


def test_question_and_review_flow(temp_db):
    workspace = db.create_workspace("Topik", "Tujuan")
    topic = db.replace_topics(
        workspace.id, [{"title": "Satu", "summary": "", "objectives": []}]
    )[0]
    question = db.save_question(
        workspace.id,
        topic.id,
        "mc",
        "Apa itu pantulan?",
        options=["A", "B", "C", "D"],
        answer=1,
        explanation="Karena berbalik arah.",
    )
    session = db.create_session(workspace.id, topic.id, "mc", [question.id])
    attempt = quiz.answer_mc(session, question, 1)
    assert attempt.is_correct is True
    assert db.get_review(question.id) is not None
    score = quiz.finish(session)
    assert score == 100
    assert db.get_session(session.id).finished_at
    assert db.get_topic(topic.id).mastery == 80
    stats = db.workspace_stats(workspace.id)
    assert stats.questions_total == 1
    assert stats.average_score == 100.0
    assert stats.streak_days >= 1


def test_due_questions_only_after_due_date(temp_db):
    workspace = db.create_workspace("Topik", "Tujuan")
    topic = db.replace_topics(
        workspace.id, [{"title": "Satu", "summary": "", "objectives": []}]
    )[0]
    question = db.save_question(workspace.id, topic.id, "mc", "Tanya", ["A", "B", "C", "D"], 0)
    db.upsert_review(question.id, "2000-01-01", 1, 2.5, 1, 0)
    assert [item.id for item in db.due_questions(workspace.id)] == [question.id]
    db.upsert_review(question.id, "2999-01-01", 3, 2.5, 2, 0)
    assert db.due_questions(workspace.id) == []


def test_chat_messages_limit_keeps_newest_in_order(temp_db):
    workspace = db.create_workspace("Topik", "Tujuan")
    chat = db.create_chat(workspace.id, title="Uji")
    for index in range(5):
        db.add_message(chat.id, "user", f"pesan {index}")
    recent = db.list_messages(chat.id, limit=3)
    assert [message.content for message in recent] == ["pesan 2", "pesan 3", "pesan 4"]
    db.delete_chat(chat.id)
    assert db.list_messages(chat.id) == []


def test_delete_workspace_cascades(temp_db):
    workspace = db.create_workspace("Topik", "Tujuan")
    topic = db.replace_topics(
        workspace.id, [{"title": "Satu", "summary": "", "objectives": []}]
    )[0]
    db.save_lesson(topic.id, {"title": "Materi"})
    db.save_question(workspace.id, topic.id, "essay", "Jelaskan", key_points=["a"])
    db.delete_workspace(workspace.id)
    assert db.get_workspace(workspace.id) is None
    assert db.list_topics(workspace.id) == []
    assert db.list_questions(workspace.id) == []