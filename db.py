"""SQLite storage for LearnAnythink.

One connection per operation keeps Streamlit reruns simple; WAL mode plus a
short busy timeout is enough for a single-user local app.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterator, Optional

from models import (
    Attempt,
    Chat,
    JournalEntry,
    Lesson,
    Message,
    Question,
    QuizSession,
    Review,
    STATUS_MASTERED,
    STATUS_TODO,
    Topic,
    Workspace,
    WorkspaceStats,
    new_id,
    now_iso,
    today_iso,
)

DEFAULT_DB_PATH = Path(".data") / "learning.db"
SCHEMA_VERSION = "1"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    goal TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'pemula',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    objectives TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'todo',
    mastery INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_topics_workspace ON topics(workspace_id, position);

CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    model TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_lessons_topic ON lessons(topic_id, created_at DESC);

CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
    title TEXT NOT NULL DEFAULT 'Percakapan baru',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chats_workspace ON chats(workspace_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    meta TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, created_at);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    options TEXT NOT NULL DEFAULT '[]',
    answer INTEGER NOT NULL DEFAULT -1,
    explanation TEXT NOT NULL DEFAULT '',
    key_points TEXT NOT NULL DEFAULT '[]',
    model_answer TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'lesson',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_questions_workspace ON questions(workspace_id, created_at DESC);

CREATE TABLE IF NOT EXISTS quiz_sessions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
    kind TEXT NOT NULL,
    question_ids TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    finished_at TEXT,
    score INTEGER
);
CREATE INDEX IF NOT EXISTS idx_sessions_workspace ON quiz_sessions(workspace_id, created_at DESC);

CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL DEFAULT '',
    is_correct INTEGER,
    points INTEGER,
    feedback TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_attempts_question ON attempts(question_id, created_at DESC);

CREATE TABLE IF NOT EXISTS reviews (
    question_id TEXT PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
    due_at TEXT NOT NULL,
    interval_days INTEGER NOT NULL DEFAULT 1,
    ease REAL NOT NULL DEFAULT 2.5,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_reviews_due ON reviews(due_at);

CREATE TABLE IF NOT EXISTS journal (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    kind TEXT NOT NULL DEFAULT 'note',
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_journal_workspace ON journal(workspace_id, created_at DESC);
"""


def db_path() -> Path:
    return Path(os.environ.get("LA_DB_PATH", str(DEFAULT_DB_PATH)))


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init(path: Optional[Path] = None) -> None:
    if path is not None:
        os.environ["LA_DB_PATH"] = str(path)
    with connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (SCHEMA_VERSION,),
        )


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _loads(raw: Any, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(str(raw))
    except (TypeError, ValueError):
        return fallback


def _workspace(row: sqlite3.Row) -> Workspace:
    return Workspace(
        id=row["id"],
        title=row["title"],
        goal=row["goal"],
        level=row["level"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        archived=bool(row["archived"]),
    )


def _topic(row: sqlite3.Row) -> Topic:
    return Topic(
        id=row["id"],
        workspace_id=row["workspace_id"],
        position=row["position"],
        title=row["title"],
        summary=row["summary"],
        objectives=_loads(row["objectives"], []),
        status=row["status"],
        mastery=int(row["mastery"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _lesson(row: sqlite3.Row) -> Lesson:
    return Lesson(
        id=row["id"],
        topic_id=row["topic_id"],
        body=_loads(row["body"], {}),
        model=row["model"],
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    )


def _chat(row: sqlite3.Row) -> Chat:
    return Chat(
        id=row["id"],
        workspace_id=row["workspace_id"],
        topic_id=row["topic_id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _message(row: sqlite3.Row) -> Message:
    return Message(
        id=row["id"],
        chat_id=row["chat_id"],
        role=row["role"],
        content=row["content"],
        created_at=row["created_at"],
        meta=_loads(row["meta"], {}),
    )


def _question(row: sqlite3.Row) -> Question:
    return Question(
        id=row["id"],
        workspace_id=row["workspace_id"],
        topic_id=row["topic_id"],
        kind=row["kind"],
        text=row["text"],
        options=_loads(row["options"], []),
        answer=int(row["answer"]),
        explanation=row["explanation"],
        key_points=_loads(row["key_points"], []),
        model_answer=row["model_answer"],
        source=row["source"],
        created_at=row["created_at"],
    )


def _session(row: sqlite3.Row) -> QuizSession:
    return QuizSession(
        id=row["id"],
        workspace_id=row["workspace_id"],
        topic_id=row["topic_id"],
        kind=row["kind"],
        question_ids=_loads(row["question_ids"], []),
        created_at=row["created_at"],
        finished_at=row["finished_at"],
        score=row["score"],
    )


def _attempt(row: sqlite3.Row) -> Attempt:
    correct = row["is_correct"]
    return Attempt(
        id=row["id"],
        session_id=row["session_id"],
        question_id=row["question_id"],
        answer_text=row["answer_text"],
        is_correct=None if correct is None else bool(correct),
        points=row["points"],
        feedback=row["feedback"],
        created_at=row["created_at"],
    )


# --------------------------------------------------------------------------- #
# workspaces
# --------------------------------------------------------------------------- #
def list_workspaces(include_archived: bool = False) -> list[Workspace]:
    query = "SELECT * FROM workspaces"
    params: list[Any] = []
    if not include_archived:
        query += " WHERE archived = 0"
    query += " ORDER BY updated_at DESC"
    with connect() as conn:
        return [_workspace(row) for row in conn.execute(query, params)]


def get_workspace(workspace_id: str) -> Optional[Workspace]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    return _workspace(row) if row else None


def create_workspace(title: str, goal: str, level: str = "pemula") -> Workspace:
    workspace = Workspace(
        id=new_id(),
        title=title.strip() or "Workspace baru",
        goal=goal.strip(),
        level=level,
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO workspaces(id, title, goal, level, created_at, updated_at, archived) "
            "VALUES(?, ?, ?, ?, ?, ?, 0)",
            (
                workspace.id,
                workspace.title,
                workspace.goal,
                workspace.level,
                workspace.created_at,
                workspace.updated_at,
            ),
        )
    return workspace


def update_workspace(workspace_id: str, **fields: Any) -> None:
    allowed = {"title", "goal", "level", "archived"}
    values = {key: value for key, value in fields.items() if key in allowed}
    if not values:
        return
    if "archived" in values:
        values["archived"] = int(bool(values["archived"]))
    values["updated_at"] = now_iso()
    assignments = ", ".join(f"{key} = ?" for key in values)
    with connect() as conn:
        conn.execute(
            f"UPDATE workspaces SET {assignments} WHERE id = ?",
            (*values.values(), workspace_id),
        )


def delete_workspace(workspace_id: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))


# --------------------------------------------------------------------------- #
# topics
# --------------------------------------------------------------------------- #
def list_topics(workspace_id: str) -> list[Topic]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM topics WHERE workspace_id = ? ORDER BY position, created_at",
            (workspace_id,),
        ).fetchall()
    return [_topic(row) for row in rows]


def get_topic(topic_id: str) -> Optional[Topic]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
    return _topic(row) if row else None


def _next_position(conn: sqlite3.Connection, workspace_id: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 AS n FROM topics WHERE workspace_id = ?",
        (workspace_id,),
    ).fetchone()
    return int(row["n"]) if row else 0


def replace_topics(workspace_id: str, items: list[dict]) -> list[Topic]:
    """Rebuild the path. Lessons of removed topics are deleted by cascade."""
    stamp = now_iso()
    with connect() as conn:
        conn.execute("DELETE FROM topics WHERE workspace_id = ?", (workspace_id,))
        for position, item in enumerate(items):
            conn.execute(
                "INSERT INTO topics(id, workspace_id, position, title, summary, objectives, "
                "status, mastery, created_at, updated_at) VALUES(?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
                (
                    new_id(),
                    workspace_id,
                    position,
                    str(item.get("title", "")).strip() or f"Topik {position + 1}",
                    str(item.get("summary", "")).strip(),
                    _json(list(item.get("objectives", []))),
                    STATUS_TODO,
                    stamp,
                    stamp,
                ),
            )
        conn.execute("UPDATE workspaces SET updated_at = ? WHERE id = ?", (stamp, workspace_id))
    return list_topics(workspace_id)


def create_topic(
    workspace_id: str,
    title: str,
    summary: str = "",
    objectives: Optional[list[str]] = None,
) -> Topic:
    stamp = now_iso()
    with connect() as conn:
        position = _next_position(conn, workspace_id)
        conn.execute(
            "INSERT INTO topics(id, workspace_id, position, title, summary, objectives, "
            "status, mastery, created_at, updated_at) VALUES(?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
            (
                new_id(),
                workspace_id,
                position,
                title.strip() or f"Topik {position + 1}",
                summary.strip(),
                _json(objectives or []),
                STATUS_TODO,
                stamp,
                stamp,
            ),
        )
        conn.execute("UPDATE workspaces SET updated_at = ? WHERE id = ?", (stamp, workspace_id))
        row = conn.execute(
            "SELECT * FROM topics WHERE workspace_id = ? ORDER BY position DESC LIMIT 1",
            (workspace_id,),
        ).fetchone()
    return _topic(row)


def update_topic(topic_id: str, **fields: Any) -> None:
    allowed = {"title", "summary", "objectives", "status", "mastery", "position"}
    values: dict[str, Any] = {}
    for key, value in fields.items():
        if key not in allowed:
            continue
        if key in {"objectives"}:
            values[key] = _json(list(value))
        elif key in {"mastery", "position"}:
            values[key] = int(value)
        else:
            values[key] = value
    if not values:
        return
    values["updated_at"] = now_iso()
    assignments = ", ".join(f"{key} = ?" for key in values)
    with connect() as conn:
        conn.execute(f"UPDATE topics SET {assignments} WHERE id = ?", (*values.values(), topic_id))


def move_topic(topic_id: str, direction: int) -> None:
    topic = get_topic(topic_id)
    if topic is None:
        return
    with connect() as conn:
        neighbour = conn.execute(
            "SELECT * FROM topics WHERE workspace_id = ? AND position = ?",
            (topic.workspace_id, topic.position + direction),
        ).fetchone()
        if neighbour is None:
            return
        stamp = now_iso()
        conn.execute(
            "UPDATE topics SET position = ?, updated_at = ? WHERE id = ?",
            (neighbour["position"], stamp, topic.id),
        )
        conn.execute(
            "UPDATE topics SET position = ?, updated_at = ? WHERE id = ?",
            (topic.position, stamp, neighbour["id"]),
        )


def delete_topic(topic_id: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))


# --------------------------------------------------------------------------- #
# lessons
# --------------------------------------------------------------------------- #
def latest_lesson(topic_id: str) -> Optional[Lesson]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM lessons WHERE topic_id = ? ORDER BY created_at DESC LIMIT 1",
            (topic_id,),
        ).fetchone()
    return _lesson(row) if row else None


def get_lesson(lesson_id: str) -> Optional[Lesson]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    return _lesson(row) if row else None


def save_lesson(topic_id: str, body: dict, model: str = "") -> Lesson:
    lesson = Lesson(id=new_id(), topic_id=topic_id, body=body, model=model)
    with connect() as conn:
        conn.execute(
            "INSERT INTO lessons(id, topic_id, body, model, created_at, completed_at) "
            "VALUES(?, ?, ?, ?, ?, NULL)",
            (lesson.id, topic_id, _json(body), model, lesson.created_at),
        )
        conn.execute(
            "UPDATE topics SET updated_at = ? WHERE id = ?", (lesson.created_at, topic_id)
        )
    return lesson


def complete_lesson(lesson_id: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE lessons SET completed_at = ? WHERE id = ? AND completed_at IS NULL",
            (now_iso(), lesson_id),
        )


# --------------------------------------------------------------------------- #
# chats & messages
# --------------------------------------------------------------------------- #
def create_chat(workspace_id: str, topic_id: Optional[str] = None, title: str = "") -> Chat:
    chat = Chat(
        id=new_id(),
        workspace_id=workspace_id,
        topic_id=topic_id,
        title=title.strip() or "Percakapan baru",
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO chats(id, workspace_id, topic_id, title, created_at, updated_at) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            (
                chat.id,
                chat.workspace_id,
                chat.topic_id,
                chat.title,
                chat.created_at,
                chat.updated_at,
            ),
        )
    return chat


def get_chat(chat_id: str) -> Optional[Chat]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
    return _chat(row) if row else None


def latest_chat(workspace_id: str) -> Optional[Chat]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM chats WHERE workspace_id = ? ORDER BY updated_at DESC LIMIT 1",
            (workspace_id,),
        ).fetchone()
    return _chat(row) if row else None


def touch_chat(chat_id: str, title: Optional[str] = None) -> None:
    with connect() as conn:
        if title:
            conn.execute(
                "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
                (title, now_iso(), chat_id),
            )
        else:
            conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (now_iso(), chat_id))


def delete_chat(chat_id: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))


def add_message(chat_id: str, role: str, content: str, meta: Optional[dict] = None) -> Message:
    message = Message(
        id=new_id(),
        chat_id=chat_id,
        role=role,
        content=content,
        meta=meta or {},
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO messages(id, chat_id, role, content, created_at, meta) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            (
                message.id,
                chat_id,
                role,
                content,
                message.created_at,
                _json(message.meta),
            ),
        )
        conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (message.created_at, chat_id))
    return message


def list_messages(chat_id: str, limit: Optional[int] = None) -> list[Message]:
    query = "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at, rowid"
    params: list[Any] = [chat_id]
    if limit:
        query = (
            "SELECT * FROM (SELECT rowid AS _rowid, * FROM messages WHERE chat_id = ? "
            "ORDER BY created_at DESC, _rowid DESC LIMIT ?) ORDER BY created_at, _rowid"
        )
        params.append(int(limit))
    with connect() as conn:
        return [_message(row) for row in conn.execute(query, params)]


# --------------------------------------------------------------------------- #
# questions
# --------------------------------------------------------------------------- #
def save_question(
    workspace_id: str,
    topic_id: Optional[str],
    kind: str,
    text: str,
    options: Optional[list[str]] = None,
    answer: int = -1,
    explanation: str = "",
    key_points: Optional[list[str]] = None,
    model_answer: str = "",
    source: str = "lesson",
) -> Question:
    question = Question(
        id=new_id(),
        workspace_id=workspace_id,
        topic_id=topic_id,
        kind=kind,
        text=text.strip(),
        options=[str(option).strip() for option in (options or [])],
        answer=int(answer),
        explanation=explanation.strip(),
        key_points=[str(point).strip() for point in (key_points or [])],
        model_answer=model_answer.strip(),
        source=source,
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO questions(id, workspace_id, topic_id, kind, text, options, answer, "
            "explanation, key_points, model_answer, source, created_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                question.id,
                question.workspace_id,
                question.topic_id,
                question.kind,
                question.text,
                _json(question.options),
                question.answer,
                question.explanation,
                _json(question.key_points),
                question.model_answer,
                question.source,
                question.created_at,
            ),
        )
    return question


def get_question(question_id: str) -> Optional[Question]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    return _question(row) if row else None


def list_questions(
    workspace_id: str,
    topic_id: Optional[str] = None,
    kind: Optional[str] = None,
    search: str = "",
) -> list[Question]:
    query = "SELECT * FROM questions WHERE workspace_id = ?"
    params: list[Any] = [workspace_id]
    if topic_id:
        query += " AND topic_id = ?"
        params.append(topic_id)
    if kind:
        query += " AND kind = ?"
        params.append(kind)
    if search.strip():
        query += " AND text LIKE ?"
        params.append(f"%{search.strip()}%")
    query += " ORDER BY created_at DESC"
    with connect() as conn:
        return [_question(row) for row in conn.execute(query, params)]


def questions_by_ids(ids: list[str]) -> list[Question]:
    if not ids:
        return []
    placeholders = ", ".join("?" for _ in ids)
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM questions WHERE id IN ({placeholders})", ids
        ).fetchall()
    by_id = {row["id"]: _question(row) for row in rows}
    return [by_id[item] for item in ids if item in by_id]


def count_questions(workspace_id: str) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM questions WHERE workspace_id = ?", (workspace_id,)
        ).fetchone()
    return int(row["n"]) if row else 0


def delete_question(question_id: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))


# --------------------------------------------------------------------------- #
# quiz sessions & attempts
# --------------------------------------------------------------------------- #
def create_session(
    workspace_id: str,
    topic_id: Optional[str],
    kind: str,
    question_ids: list[str],
) -> QuizSession:
    session = QuizSession(
        id=new_id(),
        workspace_id=workspace_id,
        topic_id=topic_id,
        kind=kind,
        question_ids=list(question_ids),
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO quiz_sessions(id, workspace_id, topic_id, kind, question_ids, "
            "created_at, finished_at, score) VALUES(?, ?, ?, ?, ?, ?, NULL, NULL)",
            (
                session.id,
                session.workspace_id,
                session.topic_id,
                session.kind,
                _json(session.question_ids),
                session.created_at,
            ),
        )
    return session


def get_session(session_id: str) -> Optional[QuizSession]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM quiz_sessions WHERE id = ?", (session_id,)).fetchone()
    return _session(row) if row else None


def finish_session(session_id: str, score: int) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE quiz_sessions SET finished_at = ?, score = ? WHERE id = ?",
            (now_iso(), int(score), session_id),
        )


def list_sessions(workspace_id: str, limit: int = 20) -> list[QuizSession]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM quiz_sessions WHERE workspace_id = ? ORDER BY created_at DESC LIMIT ?",
            (workspace_id, int(limit)),
        ).fetchall()
    return [_session(row) for row in rows]


def scores_for_topic(topic_id: str) -> list[int]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT score FROM quiz_sessions WHERE topic_id = ? AND score IS NOT NULL "
            "ORDER BY created_at",
            (topic_id,),
        ).fetchall()
    return [int(row["score"]) for row in rows]


def add_attempt(
    session_id: str,
    question_id: str,
    answer_text: str = "",
    is_correct: Optional[bool] = None,
    points: Optional[int] = None,
    feedback: str = "",
) -> Attempt:
    attempt = Attempt(
        id=new_id(),
        session_id=session_id,
        question_id=question_id,
        answer_text=answer_text,
        is_correct=is_correct,
        points=points,
        feedback=feedback,
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO attempts(id, session_id, question_id, answer_text, is_correct, "
            "points, feedback, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (
                attempt.id,
                attempt.session_id,
                attempt.question_id,
                attempt.answer_text,
                None if attempt.is_correct is None else int(attempt.is_correct),
                attempt.points,
                attempt.feedback,
                attempt.created_at,
            ),
        )
    return attempt


def get_attempt(session_id: str, question_id: str) -> Optional[Attempt]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM attempts WHERE session_id = ? AND question_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (session_id, question_id),
        ).fetchone()
    return _attempt(row) if row else None


def list_attempts(session_id: str) -> list[Attempt]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM attempts WHERE session_id = ? ORDER BY created_at", (session_id,)
        ).fetchall()
    return [_attempt(row) for row in rows]


def recent_mistakes(workspace_id: str, limit: int = 5) -> list[Question]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT q.* FROM attempts a "
            "JOIN questions q ON q.id = a.question_id "
            "JOIN quiz_sessions s ON s.id = a.session_id "
            "WHERE s.workspace_id = ? AND (a.is_correct = 0 OR (a.points IS NOT NULL AND a.points < 70)) "
            "GROUP BY q.id ORDER BY MAX(a.created_at) DESC LIMIT ?",
            (workspace_id, int(limit)),
        ).fetchall()
    return [_question(row) for row in rows]


# --------------------------------------------------------------------------- #
# reviews
# --------------------------------------------------------------------------- #
def upsert_review(
    question_id: str,
    due_at: str,
    interval_days: int,
    ease: float,
    reps: int,
    lapses: int,
) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO reviews(question_id, due_at, interval_days, ease, reps, lapses) "
            "VALUES(?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(question_id) DO UPDATE SET due_at=excluded.due_at, "
            "interval_days=excluded.interval_days, ease=excluded.ease, "
            "reps=excluded.reps, lapses=excluded.lapses",
            (question_id, due_at, int(interval_days), float(ease), int(reps), int(lapses)),
        )


def get_review(question_id: str) -> Optional[Review]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE question_id = ?", (question_id,)).fetchone()
    if row is None:
        return None
    return Review(
        question_id=row["question_id"],
        due_at=row["due_at"],
        interval_days=int(row["interval_days"]),
        ease=float(row["ease"]),
        reps=int(row["reps"]),
        lapses=int(row["lapses"]),
    )


def due_questions(workspace_id: str, limit: int = 30) -> list[Question]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT q.* FROM questions q JOIN reviews r ON r.question_id = q.id "
            "WHERE q.workspace_id = ? AND r.due_at <= ? ORDER BY r.due_at, q.created_at LIMIT ?",
            (workspace_id, today_iso(), int(limit)),
        ).fetchall()
    return [_question(row) for row in rows]


def count_due(workspace_id: str) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM reviews r JOIN questions q ON q.id = r.question_id "
            "WHERE q.workspace_id = ? AND r.due_at <= ?",
            (workspace_id, today_iso()),
        ).fetchone()
    return int(row["n"]) if row else 0


# --------------------------------------------------------------------------- #
# journal & stats
# --------------------------------------------------------------------------- #
def add_journal(workspace_id: str, kind: str, content: str) -> JournalEntry:
    entry = JournalEntry(
        id=new_id(),
        workspace_id=workspace_id,
        kind=kind,
        content=content.strip(),
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO journal(id, workspace_id, kind, content, created_at) VALUES(?, ?, ?, ?, ?)",
            (entry.id, entry.workspace_id, entry.kind, entry.content, entry.created_at),
        )
    return entry


def list_journal(workspace_id: str, limit: int = 50) -> list[JournalEntry]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM journal WHERE workspace_id = ? ORDER BY created_at DESC LIMIT ?",
            (workspace_id, int(limit)),
        ).fetchall()
    return [
        JournalEntry(
            id=row["id"],
            workspace_id=row["workspace_id"],
            kind=row["kind"],
            content=row["content"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def _streak(workspace_id: str) -> int:
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(a.created_at, 1, 10) AS day FROM attempts a "
            "JOIN quiz_sessions s ON s.id = a.session_id WHERE s.workspace_id = ? "
            "UNION SELECT DISTINCT substr(created_at, 1, 10) AS day FROM journal "
            "WHERE workspace_id = ?",
            (workspace_id, workspace_id),
        ).fetchall()
    days = {str(row["day"]) for row in rows if row["day"]}
    if not days:
        return 0
    cursor = date.today()
    if cursor.isoformat() not in days:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor.isoformat() in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def workspace_stats(workspace_id: str) -> WorkspaceStats:
    topics = list_topics(workspace_id)
    with connect() as conn:
        avg_row = conn.execute(
            "SELECT AVG(score) AS avg FROM quiz_sessions WHERE workspace_id = ? AND score IS NOT NULL",
            (workspace_id,),
        ).fetchone()
        question_row = conn.execute(
            "SELECT COUNT(*) AS n FROM questions WHERE workspace_id = ?", (workspace_id,)
        ).fetchone()
    average = float(avg_row["avg"]) if avg_row and avg_row["avg"] is not None else None
    return WorkspaceStats(
        topics_total=len(topics),
        topics_mastered=sum(1 for topic in topics if topic.status == STATUS_MASTERED),
        questions_total=int(question_row["n"]) if question_row else 0,
        due_reviews=count_due(workspace_id),
        average_score=round(average, 1) if average is not None else None,
        streak_days=_streak(workspace_id),
    )


def delete_all_data() -> None:
    with connect() as conn:
        for table in (
            "journal",
            "reviews",
            "attempts",
            "quiz_sessions",
            "questions",
            "messages",
            "chats",
            "lessons",
            "topics",
            "workspaces",
        ):
            conn.execute(f"DELETE FROM {table}")
