"""Guards for user-facing copy and theme choices."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
)


def _has_emoji(text: str) -> bool:
    for char in text:
        point = ord(char)
        if point == 0xFE0F:
            return True
        if any(start <= point <= end for start, end in EMOJI_RANGES):
            return True
    return False


def test_ui_source_has_no_emoji():
    paths = [ROOT / "streamlit_app.py"]
    paths += sorted((ROOT / "views").glob("*.py"))
    paths += sorted((ROOT / "ui").glob("*.py"))

    offenders = []
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _has_emoji(line):
                offenders.append(f"{path.name}:{number}")

    assert not offenders, "emoji tersisa di UI: " + ", ".join(offenders)


def test_theme_is_dark():
    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert config["theme"]["base"] == "dark"
    assert config["theme"]["primaryColor"] == "#2E7D5B"
    assert config["theme"]["linkColor"] == "#4ADD82"


def test_brand_assets_are_transparent():
    from PIL import Image

    for name in ("symbol-color.png", "lockup-horizontal-dark-transparent.png"):
        path = ROOT / "Logo Kit" / "png" / name
        assert path.exists(), f"aset logo hilang: {name}"
        image = Image.open(path)
        assert image.mode == "RGBA", f"{name} harus punya kanal alpha"
        assert image.getchannel("A").getextrema()[0] < 255, f"{name} harus transparan"