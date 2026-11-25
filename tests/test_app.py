"""End-to-end test through Streamlit's AppTest harness (no network calls)."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

import db
from services import learning

ROOT = Path(__file__).resolve().parents[1]


def _button(at: AppTest, label: str):
    matches = [button for button in at.button if button.label == label]
    assert matches, f"tombol {label!r} tidak ditemukan"
    return matches[0]


def test_app_loads(temp_db, monkeypatch):
    """Test that the app loads without errors."""

    # Mock LLM calls to avoid network
    def mock_generate_path(workspace):
        return [
            {"title": "Topik 1", "summary": "Ringkasan 1", "objectives": ["Obj 1"]},
            {"title": "Topik 2", "summary": "Ringkasan 2", "objectives": ["Obj 2"]},
            {"title": "Topik 3", "summary": "Ringkasan 3", "objectives": ["Obj 3"]},
        ]

    monkeypatch.setattr(learning, "generate_path", mock_generate_path)

    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    at.run()
    assert not at.exception
    assert any("Belum ada ruang belajar" in item.value for item in at.caption)

    # Create a workspace through the form. Form values only stick if the form
    # is submitted in the same run, so no at.run() between set_value and click.
    at.text_area(key="home_new_goal").set_value("Belajar Python dasar")
    at.selectbox(key="home_new_level").set_value("pemula")
    _button(at, "Mulai belajar").click().run()
    assert not at.exception

    workspaces = db.list_workspaces()
    assert len(workspaces) == 1
    workspace = workspaces[0]
    assert workspace.goal == "Belajar Python dasar"