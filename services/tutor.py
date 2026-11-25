"""Assemble workspace context and stream tutor replies."""

from __future__ import annotations

from typing import Iterator, Optional

import db
from models import Topic, Workspace
from services import attachments as attachment_service
from services import learning, llm
from services.prompts import TUTOR

CONTEXT_LIMIT = 7_000
HISTORY_LIMIT = 14


def build_context(workspace: Workspace, topic: Optional[Topic]) -> str:
    parts = [
        f"Tujuan workspace: {workspace.goal}",
        f"Level pelajar: {workspace.level}",
        "Peta topik:",
    ]
    for item in db.list_topics(workspace.id):
        parts.append(
            f"{item.position + 1}. [{item.status_label}, mastery {item.mastery}] "
            f"{item.title} — {item.summary}"
        )
    if topic:
        parts.append(f"\nTopik aktif: {topic.title}")
        if topic.objectives:
            parts.append("Objectives: " + "; ".join(topic.objectives))
        lesson = db.latest_lesson(topic.id)
        if lesson:
            parts.append("Ringkasan materi:\n" + learning.lesson_text(lesson)[:2_000])
    mistakes = db.recent_mistakes(workspace.id, limit=5)
    if mistakes:
        parts.append("\nKesalahan terakhir yang perlu diperbaiki:")
        for question in mistakes:
            if question.options and 0 <= question.answer < len(question.options):
                correct = question.options[question.answer]
            else:
                correct = question.model_answer or "lihat materi"
            parts.append(f"- {question.text}\n  Jawaban benar: {correct}")
    return "\n".join(parts)[:CONTEXT_LIMIT]


def history(chat_id: str, limit: int = HISTORY_LIMIT) -> list[dict]:
    messages = db.list_messages(chat_id, limit=limit)
    return [{"role": message.role, "content": message.content} for message in messages]


def reply(
    chat_id: str,
    workspace: Workspace,
    topic: Optional[Topic],
    user_text: str,
    batch: Optional[attachment_service.AttachmentBatch] = None,
) -> Iterator[str]:
    batch = batch or attachment_service.AttachmentBatch()
    context = build_context(workspace, topic)
    extra = attachment_service.context_text(batch.items)
    if extra:
        context = (context + extra)[: CONTEXT_LIMIT + 4_000]
    system = TUTOR + "\n\nKONTEKS WORKSPACE (gunakan sebagai sumber utama):\n" + context

    messages = history(chat_id)
    if not messages or messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": user_text})
    images = attachment_service.image_blocks(batch.items)
    if images:
        last = messages[-1]
        text = last["content"] if isinstance(last["content"], str) else user_text
        messages[-1] = {
            "role": "user",
            "content": [{"type": "text", "text": text}, *images],
        }

    yield from llm.stream_chat(system, messages, max_tokens=llm.MAX_TOKENS["chat"])


def title_from(text: str) -> str:
    clean = " ".join(text.split())
    if not clean:
        return "Percakapan baru"
    words = clean.split()
    title = " ".join(words[:7])
    return (title[:60] + "…") if len(title) > 60 else title
