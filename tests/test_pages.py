"""Guards for the shared page registry, nav icons, and header wiring."""

from __future__ import annotations

import re
from pathlib import Path

from streamlit.material_icon_names import ALL_MATERIAL_ICONS

from pages import PAGES, PAGE_BY_KEY

ROOT = Path(__file__).resolve().parents[1]


def test_registry_routes_exist():
    for page in PAGES:
        assert (ROOT / page.path).exists(), f"rute hilang: {page.path}"


def test_registry_keys_are_unique():
    keys = [page.key for page in PAGES]
    assert len(keys) == len(set(keys))


def test_page_icons_are_valid_material_symbols():
    for page in PAGES:
        assert page.icon in ALL_MATERIAL_ICONS, f"ikon tidak dikenal: {page.icon}"


def test_every_view_header_uses_a_registered_page():
    pattern = re.compile(r'ui\.header\("([a-z_]+)"\)')
    for path in sorted((ROOT / "views").glob("*.py")):
        for key in pattern.findall(path.read_text(encoding="utf-8")):
            assert key in PAGE_BY_KEY, f"{path.name}: header {key!r} tidak terdaftar"


def test_header_reuses_the_sidebar_icon():
    text = (ROOT / "ui" / "layout.py").read_text(encoding="utf-8")
    assert ":material/{entry.icon}:" in text
    assert "PAGE_BY_KEY" in text