"""Quiz generation, essay grading, scoring, and the SM-2 review schedule."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import db
from models import (
    Question,
    QuizSession,
    Review,
    Topic,
    Workspace,
)
from services import llm, learning
from services.prompts import ESSAY_PROMPT, GRADE_PROMPT, MC_PROMPT, TUTOR
from services.schemas import EssayGrades, EssayQuiz, MCQuiz

DIFFICULTIES = ("mudah", "sedang", "sulit")


# --------------------------------------------------------------------------- #
# generation
# --------------------------------------------------------------------------- #
def _context(topic: Optional[Topic], workspace: Workspace) -> str:
    if topic is None:
        parts = [f"Tujuan workspace: {workspace.goal}"]
        for item in db.list_topics(workspace.id):
            parts.append(f"{item.position + 1}. {item.title} — {item.summary}")
            lesson = db.latest_lesson(item.id)
            if lesson:
                parts.append(learning.lesson_text(lesson)[:900])
        return "\n".join(parts)[:7_000]
    lesson = db.latest_lesson(topic.id)
    if lesson:
        return learning.lesson_text(lesson)
    return (
        f"{topic.title}\n{topic.summary}\n"
        + "\n".join(f"- {point}" for point in topic.objectives)
    )


def _existing_texts(workspace_id: str, topic_id: Optional[str], kind: str) -> list[str]:
    return [
        question.text
        for question in db.list_questions(workspace_id, topic_id=topic_id, kind=kind)[:20]
    ]


def _tidy_mc(result: MCQuiz, count: int) -> list[dict]:
    items = []
    seen: set[str] = set()
    for item in result.questions:
        text = " ".join(item.text.split())
        options = [" ".join(str(option).split()) for option in item.options]
        if not text or len(options) != 4 or not 0 <= item.answer <= 3:
            continue
        if not all(options):
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(
            {
                "text": text,
                "options": options,
                "answer": int(item.answer),
                "explanation": " ".join(item.explanation.split()),
            }
        )
    if not items:
        raise llm.LLMError("Model tidak menghasilkan soal pilihan ganda yang valid.")
    return items[:count]


def _tidy_essay(result: EssayQuiz, count: int) -> list[dict]:
    items = []
    seen: set[str] = set()
    for item in result.questions:
        text = " ".join(item.text.split())
        points = [" ".join(str(point).split()) for point in item.key_points if str(point).strip()]
        if not text or len(points) < 2:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(
            {
                "text": text,
                "key_points": points[:4],
                "model_answer": " ".join(item.model_answer.split()),
            }
        )
    if not items:
        raise llm.LLMError("Model tidak menghasilkan soal esai yang valid.")
    return items[:count]


def generate(
    workspace: Workspace,
    topic: Optional[Topic],
    kind: str,
    count: int,
    difficulty: str = "sedang",
) -> list[dict]:
    count = max(1, min(10, int(count)))
    topic_id = topic.id if topic else None
    excluded = "\n".join(f"- {text}" for text in _existing_texts(workspace.id, topic_id, kind))
    prompt = (MC_PROMPT if kind == "mc" else ESSAY_PROMPT).format(
        topic=topic.title if topic else workspace.goal,
        lesson=_context(topic, workspace),
        count=count,
        difficulty=difficulty,
        excluded=excluded or "- (belum ada)",
    )
    if kind == "mc":
        schema = llm.json_call(TUTOR, prompt, MCQuiz, llm.MAX_TOKENS["quiz"])
        return _tidy_mc(schema, count)
    schema = llm.json_call(TUTOR, prompt, EssayQuiz, llm.MAX_TOKENS["quiz"])
    return _tidy_essay(schema, count)


def save_questions(
    workspace_id: str,
    topic_id: Optional[str],
    kind: str,
    items: list[dict],
) -> list[Question]:
    saved = []
    for item in items:
        saved.append(
            db.save_question(
                workspace_id=workspace_id,
                topic_id=topic_id,
                kind=kind,
                text=item["text"],
                options=item.get("options", []),
                answer=int(item.get("answer", -1)),
                explanation=item.get("explanation", ""),
                key_points=item.get("key_points", []),
                model_answer=item.get("model_answer", ""),
                source="lesson",
            )
        )
    return saved


def create_quiz(
    workspace: Workspace,
    topic: Optional[Topic],
    kind: str,
    count: int,
    difficulty: str = "sedang",
) -> QuizSession:
    items = generate(workspace, topic, kind, count, difficulty)
    questions = save_questions(workspace.id, topic.id if topic else None, kind, items)
    return db.create_session(
        workspace_id=workspace.id,
        topic_id=topic.id if topic else None,
        kind=kind,
        question_ids=[question.id for question in questions],
    )


def create_review_session(workspace: Workspace, limit: int = 10) -> Optional[QuizSession]:
    questions = db.due_questions(workspace.id, limit=limit)
    if not questions:
        return None
    return db.create_session(
        workspace_id=workspace.id,
        topic_id=None,
        kind="mixed",
        question_ids=[question.id for question in questions],
    )


# --------------------------------------------------------------------------- #
# attempts & scoring
# --------------------------------------------------------------------------- #
def attempts_map(session_id: str) -> dict[str, object]:
    return {attempt.question_id: attempt for attempt in db.list_attempts(session_id)}


def progress(session: QuizSession) -> tuple[int, int]:
    return len(db.list_attempts(session.id)), len(db.questions_by_ids(session.question_ids))


def _quality(is_correct: Optional[bool], points: Optional[int]) -> int:
    if is_correct is True:
        return 5
    if points is None:
        return 2
    if points >= 85:
        return 5
    if points >= 70:
        return 4
    if points >= 50:
        return 3
    return 2


def next_review(review: Optional[Review], quality: int) -> Review:
    ease = review.ease if review else 2.5
    interval = review.interval_days if review else 1
    reps = review.reps if review else 0
    lapses = review.lapses if review else 0
    if quality < 3:
        reps = 0
        interval = 1
        lapses += 1
    else:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 3
        else:
            interval = max(1, round(interval * ease))
        reps += 1
    ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease = max(1.3, min(2.8, ease))
    due = (date.today() + timedelta(days=interval)).isoformat()
    return Review(
        question_id=review.question_id if review else "",
        due_at=due,
        interval_days=interval,
        ease=round(ease, 2),
        reps=reps,
        lapses=lapses,
    )


def record_attempt(
    session: QuizSession,
    question: Question,
    answer_text: str = "",
    is_correct: Optional[bool] = None,
    points: Optional[int] = None,
    feedback: str = "",
) -> object:
    attempt = db.add_attempt(
        session_id=session.id,
        question_id=question.id,
        answer_text=answer_text,
        is_correct=is_correct,
        points=points,
        feedback=feedback,
    )
    quality = _quality(is_correct, points)
    review = next_review(db.get_review(question.id), quality)
    review.question_id = question.id
    db.upsert_review(
        question.id,
        review.due_at,
        review.interval_days,
        review.ease,
        review.reps,
        review.lapses,
    )
    return attempt


def answer_mc(session: QuizSession, question: Question, choice: int) -> object:
    correct = choice == question.answer
    return record_attempt(
        session,
        question,
        answer_text=str(choice),
        is_correct=correct,
        points=100 if correct else 0,
        feedback=question.explanation,
    )


def grade_essays(
    session: QuizSession,
    answers: dict[str, str],
    question_ids: Optional[list[str]] = None,
) -> None:
    ids = question_ids if question_ids is not None else session.question_ids
    questions = [question for question in db.questions_by_ids(ids) if question.kind == "essay"]
    payload = []
    for index, question in enumerate(questions):
        payload.append(
            {
                "number": index + 1,
                "question": question,
                "answer": (answers.get(question.id, "") or "").strip(),
            }
        )
    blocks = []
    for item in payload:
        question = item["question"]
        blocks.append(
            f"Nomor {item['number']}\nSoal: {question.text}\n"
            f"Poin kunci: {', '.join(question.key_points)}\n"
            f"Jawaban pelajar: {item['answer'] or '(tidak dijawab)'}"
        )
    result = llm.json_call(
        TUTOR,
        GRADE_PROMPT.format(qa="\n\n".join(blocks)),
        EssayGrades,
        llm.MAX_TOKENS["grade"],
    )
    by_number = {grade.number: grade for grade in result.grades}
    for item in payload:
        grade = by_number.get(item["number"])
        question = item["question"]
        if grade is None:
            points, verdict, feedback = 0, "salah", "Jawaban belum bisa dinilai."
        else:
            points = max(0, min(100, int(grade.points)))
            verdict = grade.verdict if grade.verdict in {"benar", "sebagian", "salah"} else "sebagian"
            feedback = grade.feedback.strip()
        record_attempt(
            session,
            question,
            answer_text=item["answer"],
            is_correct=verdict == "benar",
            points=points,
            feedback=feedback,
        )


def score(session: QuizSession) -> int:
    questions = db.questions_by_ids(session.question_ids)
    if not questions:
        return 0
    attempts = attempts_map(session.id)
    if session.kind == "mc":
        correct = sum(
            1
            for question in questions
            if question.id in attempts and getattr(attempts[question.id], "is_correct", False)
        )
        return round(correct / len(questions) * 100)
    points = []
    for question in questions:
        attempt = attempts.get(question.id)
        points.append(int(getattr(attempt, "points", 0) or 0) if attempt else 0)
    return round(sum(points) / len(points))


def ready_to_finish(session: QuizSession) -> bool:
    total = len(db.questions_by_ids(session.question_ids))
    if total == 0:
        return False
    return len(db.list_attempts(session.id)) >= total


def finish(session: QuizSession) -> int:
    final = score(session)
    db.finish_session(session.id, final)
    if session.topic_id:
        learning.refresh_topic(session.topic_id)
        topic = db.get_topic(session.topic_id)
        label = f"topik \"{topic.title}\"" if topic else "topik"
    else:
        learning.refresh_workspace(session.workspace_id)
        label = "seluruh workspace"
    db.add_journal(
        session.workspace_id,
        "quiz",
        f"Menyelesaikan latihan {label} dengan skor {final}/100.",
    )
    return final


def finish_if_ready(session: QuizSession) -> Optional[int]:
    if session.finished or not ready_to_finish(session):
        return None
    return finish(session)


def option_letter(index: int) -> str:
    return "ABCD"[index] if 0 <= index < 4 else "?"


def answer_label(question: Question, choice: int) -> str:
    if question.options and 0 <= choice < len(question.options):
        return f"{option_letter(choice)}. {question.options[choice]}"
    return "Tidak dijawab"
