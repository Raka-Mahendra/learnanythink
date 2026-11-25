"""Domain models for LearnAnythink.

Plain dataclasses so the database layer stays independent from Streamlit and
the learning engine can be tested without a running app.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional

STATUS_TODO = "todo"
STATUS_LEARNING = "learning"
STATUS_MASTERED = "mastered"

STATUS_LABELS = {
    STATUS_TODO: "Belum mulai",
    STATUS_LEARNING: "Sedang belajar",
    STATUS_MASTERED: "Paham",
}

LEVELS = ("pemula", "menengah", "lanjutan")
KINDS = ("mc", "essay")
KIND_LABELS = {"mc": "Pilihan ganda", "essay": "Esai"}


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today_iso(offset_days: int = 0) -> str:
    return (date.today() + timedelta(days=offset_days)).isoformat()


@dataclass
class Workspace:
    id: str
    title: str
    goal: str
    level: str = "pemula"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    archived: bool = False


@dataclass
class Topic:
    id: str
    workspace_id: str
    position: int
    title: str
    summary: str = ""
    objectives: list[str] = field(default_factory=list)
    status: str = STATUS_TODO
    mastery: int = 0
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, "Belum mulai")


@dataclass
class Lesson:
    id: str
    topic_id: str
    body: dict
    model: str = ""
    created_at: str = field(default_factory=now_iso)
    completed_at: Optional[str] = None

    @property
    def completed(self) -> bool:
        return bool(self.completed_at)


@dataclass
class Chat:
    id: str
    workspace_id: str
    topic_id: Optional[str] = None
    title: str = "Percakapan baru"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass
class Message:
    id: str
    chat_id: str
    role: str
    content: str
    created_at: str = field(default_factory=now_iso)
    meta: dict = field(default_factory=dict)


@dataclass
class Question:
    id: str
    workspace_id: str
    topic_id: Optional[str]
    kind: str
    text: str
    options: list[str] = field(default_factory=list)
    answer: int = -1
    explanation: str = ""
    key_points: list[str] = field(default_factory=list)
    model_answer: str = ""
    source: str = "lesson"
    created_at: str = field(default_factory=now_iso)


@dataclass
class QuizSession:
    id: str
    workspace_id: str
    topic_id: Optional[str]
    kind: str
    question_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    finished_at: Optional[str] = None
    score: Optional[int] = None

    @property
    def finished(self) -> bool:
        return bool(self.finished_at)


@dataclass
class Attempt:
    id: str
    session_id: str
    question_id: str
    answer_text: str = ""
    is_correct: Optional[bool] = None
    points: Optional[int] = None
    feedback: str = ""
    created_at: str = field(default_factory=now_iso)


@dataclass
class Review:
    question_id: str
    due_at: str
    interval_days: int = 1
    ease: float = 2.5
    reps: int = 0
    lapses: int = 0


@dataclass
class JournalEntry:
    id: str
    workspace_id: str
    kind: str
    content: str
    created_at: str = field(default_factory=now_iso)


@dataclass
class WorkspaceStats:
    topics_total: int = 0
    topics_mastered: int = 0
    questions_total: int = 0
    due_reviews: int = 0
    average_score: Optional[float] = None
    streak_days: int = 0

    @property
    def mastery_percent(self) -> int:
        if not self.topics_total:
            return 0
        return round(self.topics_mastered / self.topics_total * 100)
