"""Adaptive tutor chat with workspace context."""

from __future__ import annotations

import streamlit as st

import db
import state
from services import attachments, llm, tutor
from ui import layout as ui
from views import _common as common


def _message_meta(batch: attachments.AttachmentBatch) -> dict:
    return {
        "attachments": [
            {
                "name": item.name,
                "kind": item.kind,
                "media_type": item.media_type,
                "text": item.text[:4_000],
                "note": item.note,
            }
            for item in batch.items
        ]
    }


def render() -> None:
    ui.header("tutor")
    common.flash()
    workspace = common.require_workspace()
    if workspace is None:
        return
    topics = db.list_topics(workspace.id)
    labels = ["Seluruh ruang belajar"] + [f"{topic.position + 1}. {topic.title}" for topic in topics]
    default_index = 0
    if state.get().topic_id:
        for index, topic in enumerate(topics, start=1):
            if topic.id == state.get().topic_id:
                default_index = index
                break
    choice = st.selectbox("Topik", labels, index=default_index, key="tutor_context")
    topic = topics[default_index - 1] if default_index else None
    if choice != labels[default_index]:
        # The select box is the source of truth on this page.
        topic = next(
            (item for index, item in enumerate(topics, start=1) if labels[index] == choice),
            None,
        )
        state.select_topic(topic.id if topic else None)

    chat = state.chat()
    if chat is None:
        ui.empty_state("Chat belum siap", "Buat ruang belajar terlebih dahulu.")
        return

    with st.container(horizontal=True, gap="small"):
        if st.button("Chat baru", key="tutor_new_chat"):
            state.new_chat()
            st.rerun()
        with st.popover("Hapus chat"):
            st.write("Hapus seluruh pesan di percakapan ini?")
            if st.button("Ya, hapus", key="tutor_delete_chat", type="primary"):
                db.delete_chat(chat.id)
                state.new_chat()
                st.rerun()

    messages = db.list_messages(chat.id, limit=60)
    if len(messages) >= 60:
        st.caption("60 pesan terakhir ditampilkan.")
    if not messages:
        with st.container(border=True):
            st.write("Tanyakan konsep, minta contoh, atau minta diuji.")

    for message in messages:
        with st.chat_message(message.role):
            st.markdown(message.content)
            names = [
                item.get("name", "")
                for item in message.meta.get("attachments", [])
                if item.get("name")
            ]
            if names:
                st.caption("Lampiran: " + ", ".join(names))

    submitted = st.chat_input(
        "Tanya apa saja atau lampirkan bahan...",
        accept_file="multiple",
        file_type=[
            "png", "jpg", "jpeg", "webp", "gif",
            "txt", "md", "csv", "json", "py", "pdf",
        ],
    )
    if not submitted:
        return

    text = getattr(submitted, "text", None)
    files = getattr(submitted, "files", None)
    if text is None and isinstance(submitted, str):
        text = submitted
    text = (text or "").strip()
    files = list(files or [])
    batch = attachments.read_files(files)
    if not text and not batch.items:
        return
    if not text:
        text = "Tolong jelaskan lampiran berikut dan kaitkan dengan topik yang sedang saya pelajari."

    db.add_message(chat.id, "user", text, meta=_message_meta(batch))
    if chat.title == "Percakapan baru":
        db.touch_chat(chat.id, title=common.title_from_goal(text))
    if batch.warning:
        st.warning(batch.warning)

    with st.chat_message("user"):
        st.markdown(text)
        if batch.names():
            st.caption("Lampiran: " + ", ".join(batch.names()))

    with st.chat_message("assistant"):
        try:
            stream = tutor.reply(chat.id, workspace, topic, text, batch)
            answer = st.write_stream(stream)
        except llm.LLMError as exc:
            st.error(str(exc))
            return
    if answer and str(answer).strip():
        db.add_message(chat.id, "assistant", str(answer))
        st.rerun()
