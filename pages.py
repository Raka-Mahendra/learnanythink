"""Single source of truth for pages, their routes, and their nav icons."""

from __future__ import annotations

from typing import NamedTuple


class PageDef(NamedTuple):
    key: str
    title: str
    path: str
    icon: str


PAGES: tuple[PageDef, ...] = (
    PageDef("home", "Beranda", "routes/home.py", "home"),
    PageDef("tutor", "Tutor", "routes/tutor.py", "forum"),
    PageDef("path", "Peta Belajar", "routes/path.py", "map"),
    PageDef("lesson", "Materi", "routes/lesson.py", "menu_book"),
    PageDef("practice", "Latihan", "routes/practice.py", "edit_note"),
    PageDef("bank", "Bank Soal", "routes/bank.py", "inventory_2"),
    PageDef("progress", "Progres", "routes/progress.py", "insights"),
    PageDef("settings", "Pengaturan", "routes/settings.py", "settings"),
)

PAGE_BY_KEY = {page.key: page for page in PAGES}