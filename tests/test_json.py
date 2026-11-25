from __future__ import annotations

import pytest

from services.llm import parse_json


def test_parse_plain_json():
    assert parse_json('{"a": 1}') == {"a": 1}


def test_parse_fenced_json():
    raw = "Berikut hasilnya:\n```json\n{\"topics\": []}\n```\nSemoga membantu."
    assert parse_json(raw) == {"topics": []}


def test_parse_json_with_surrounding_text():
    assert parse_json('awal {"ok": true} akhir') == {"ok": True}


def test_parse_invalid_json_raises():
    with pytest.raises(ValueError):
        parse_json("tidak ada json di sini")