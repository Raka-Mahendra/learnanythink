"""Shared pytest setup: project on sys.path and an isolated database per test."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db  # noqa: E402


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("LA_DB_PATH", str(tmp_path / "learning.db"))
    monkeypatch.setenv("LA_DEMO", "1")
    db.init()
    return db.db_path()