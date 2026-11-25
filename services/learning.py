"""Learning path, lesson generation, and mastery calculation."""

from __future__ import annotations

from typing import Optional

import db
from models import Lesson, Topic, Workspace, STATUS_LEARNING, STATUS_MASTERED, STATUS_TODO
from services import demo, llm
from services.prompts import LESSON_PROMPT, PATH_PROMPT, TUTOR
from services.schemas import LearningPath, Lesson as LessonSchema


def _tidy_path(plan: LearningPath, existing: list[str]) -> list[dict]:
    seen = {" ".join(title.lower().split()) for title in existing}
    items: list[dict] = []
    for item in plan.topics:
        title = " ".join(item.title.split()).strip(" .:-")
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        objectives = [
            " ".join(str(point).split())
            for point in item.objectives
            if str(point).strip()
        ][:4]
        items.append(
            {
                "title": title[:80],
                "summary": " ".join(item.summary.split())[:240],
                "objectives": objectives,
            }
        )
    if len(items) < 3:
        raise llm.LLMError("Model tidak menghasilkan cukup topik. Coba susun ulang peta.")
    return items[:7]


def generate_path(workspace: Workspace) -> list[dict]:
    if llm.offline():
        return demo.path(workspace.goal)
    existing: list[str] = []
    prompt = PATH_PROMPT.format(
        goal=workspace.goal,
        level=workspace.level,
        existing="(belum ada)",
    )
    plan = llm.json_call(TUTOR, prompt, LearningPath, llm.MAX_TOKENS["path"])
    return _tidy_path(plan, existing)


def apply_path(workspace_id: str, items: list[dict]) -> list[Topic]:
    return db.replace_topics(workspace_id, items)


def start_workspace(
    title: str,
    goal: str,
    level: str = "pemula",
) -> tuple[Workspace, list[Topic]]:
    """Create the workspace, then build its path in one blocking step."""
    workspace = db.create_workspace(title=title, goal=goal, level=level)
    items = generate_path(workspace)
    topics = apply_path(workspace.id, items)
    db.add_journal(
        workspace.id,
        "milestone",
        f"Peta belajar disusun: {len(topics)} topik untuk tujuan \"{workspace.goal}\".",
    )
    return workspace, topics


# --------------------------------------------------------------------------- #
# lessons
# --------------------------------------------------------------------------- #
def _tidy_lesson(schema: LessonSchema) -> dict:
    sections = [
        {
            "heading": " ".join(section.heading.split())[:80],
            "body": section.body.strip(),
        }
        for section in schema.sections
        if section.heading.strip() and section.body.strip()
    ][:6]
    if len(sections) < 3:
        raise llm.LLMError("Materi tidak punya cukup bagian. Coba tulis ulang.")
    terms = [
        {"term": term.term.strip(), "definition": term.definition.strip()}
        for term in schema.key_terms
        if term.term.strip() and term.definition.strip()
    ][:6]
    return {
        "title": schema.title.strip() or "Materi",
        "objective": schema.objective.strip(),
        "sections": sections,
        "key_terms": terms,
        "example": schema.example.strip(),
        "recap": schema.recap.strip(),
    }


def generate_lesson(workspace: Workspace, topic: Topic) -> tuple[dict, str]:
    if llm.offline():
        return demo.lesson(topic), "mode demo"
    topics = db.list_topics(workspace.id)
    previous = [
        item.title for item in topics if item.position < topic.position
    ][-3:]
    prompt = LESSON_PROMPT.format(
        goal=workspace.goal,
        level=workspace.level,
        position=topic.position + 1,
        total=len(topics),
        title=topic.title,
        summary=topic.summary or "-",
        objectives="; ".join(topic.objectives) or "-",
        previous=", ".join(previous) if previous else "(ini topik pertama)",
    )
    schema = llm.json_call(TUTOR, prompt, LessonSchema, llm.MAX_TOKENS["lesson"])
    return _tidy_lesson(schema), llm.config().model


def save_lesson(topic_id: str, body: dict, model: str) -> Lesson:
    return db.save_lesson(topic_id, body, model)


def lesson_body(topic: Topic) -> Optional[dict]:
    lesson = db.latest_lesson(topic.id)
    return lesson.body if lesson else None


def lesson_text(lesson: Lesson) -> str:
    body = lesson.body
    lines = [str(body.get("title", "")), str(body.get("objective", ""))]
    for section in body.get("sections", []):
        lines.append(f"{section.get('heading', '')}: {section.get('body', '')}")
    for term in body.get("key_terms", []):
        lines.append(f"{term.get('term', '')} = {term.get('definition', '')}")
    lines.append(f"Contoh: {body.get('example', '')}")
    lines.append(f"Rangkuman: {body.get('recap', '')}")
    return "\n".join(line for line in lines if line)[:7_000]


def mark_lesson_complete(lesson: Lesson, topic: Topic) -> None:
    db.complete_lesson(lesson.id)
    db.add_journal(
        topic.workspace_id,
        "milestone",
        f"Menyelesaikan materi \"{topic.title}\".",
    )
    refresh_topic(topic.id)


# --------------------------------------------------------------------------- #
# mastery
# --------------------------------------------------------------------------- #
def compute_mastery(lesson_done: bool, scores: list[int]) -> tuple[int, str]:
    clean = [max(0, min(100, int(score))) for score in scores]
    lesson_part = 20 if lesson_done else 0
    best = max(clean) if clean else 0
    recent_scores = clean[-3:]
    recent = sum(recent_scores) / len(recent_scores) if recent_scores else 0
    mastery = round(lesson_part + best * 0.5 + recent * 0.3)
    mastery = max(0, min(100, mastery))
    if mastery >= 80 and lesson_done:
        status = STATUS_MASTERED
    elif lesson_done or clean:
        status = STATUS_LEARNING
    else:
        status = STATUS_TODO
    return mastery, status


def refresh_topic(topic_id: str) -> None:
    topic = db.get_topic(topic_id)
    if topic is None:
        return
    lesson = db.latest_lesson(topic_id)
    scores = db.scores_for_topic(topic_id)
    mastery, status = compute_mastery(bool(lesson and lesson.completed), scores)
    db.update_topic(topic_id, mastery=mastery, status=status)


def refresh_workspace(workspace_id: str) -> None:
    for topic in db.list_topics(workspace_id):
        refresh_topic(topic.id)
