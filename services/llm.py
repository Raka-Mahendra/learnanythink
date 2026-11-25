"""Token Harbor client.

Token Harbor exposes an OpenAI-compatible API, so one SDK covers chat
streaming and JSON-structured generations. Keys are read from
``st.secrets`` first, then the environment.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Iterator

import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv()

DEFAULT_BASE_URL = "https://tokenharbor.ai/v1"
DEFAULT_MODEL = "deepseek-v4.1-flash:free"

MAX_TOKENS = {
    "path": 1200,
    "lesson": 2600,
    "quiz": 2200,
    "grade": 1800,
    "chat": 1400,
    "title": 60,
}


class LLMError(RuntimeError):
    """A model call failed in a way the UI can explain."""


@dataclass(frozen=True)
class Config:
    api_key: str
    base_url: str
    model: str

    @property
    def ready(self) -> bool:
        return bool(self.api_key)


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
def _secret_value(name: str) -> str:
    try:
        secrets = st.secrets
    except Exception:  # noqa: BLE001 - no secrets.toml at all
        return ""
    for section in ("tokenharbor", "llm"):
        try:
            scope = secrets[section]
            value = scope[name]
            if value not in (None, ""):
                return str(value).strip()
        except Exception:  # noqa: BLE001 - section or key is optional
            continue
    try:
        value = secrets[name]
        if value not in (None, ""):
            return str(value).strip()
    except Exception:  # noqa: BLE001
        pass
    return ""


def _setting(*names: str, default: str = "") -> str:
    for name in names:
        value = _secret_value(name) or os.getenv(name, "")
        if value:
            return str(value).strip()
    return default


def config() -> Config:
    base_url = _setting(
        "TH_BASE_URL", "TOKEN_HARBOR_BASE_URL", "LA_BASE_URL", default=DEFAULT_BASE_URL
    )
    model = _setting("TH_MODEL", "TOKEN_HARBOR_MODEL", "LA_MODEL", default=DEFAULT_MODEL)
    api_key = _setting(
        "TH_API_KEY",
        "TOKEN_HARBOR_API_KEY",
        "LA_API_KEY",
    )
    return Config(api_key=api_key, base_url=base_url.rstrip("/"), model=model)


def _client() -> Any:
    from openai import OpenAI

    cfg = config()
    if not cfg.api_key:
        raise LLMError("Layanan AI belum siap. Hubungi pengelola aplikasi.")
    return OpenAI(api_key=cfg.api_key, base_url=cfg.base_url, timeout=90.0, max_retries=1)


# --------------------------------------------------------------------------- #
# transport
# --------------------------------------------------------------------------- #
def _friendly(exc: Exception) -> str:
    name = type(exc).__name__
    status = getattr(exc, "status_code", None)
    text = str(exc)
    if status in (401, 403) or "Authentication" in name or "PermissionDenied" in name:
        return "Akses AI ditolak. Periksa pengaturan akun atau hubungi pengelola."
    if status == 429 or "RateLimit" in name:
        return "Batas penggunaan AI tercapai. Tunggu sebentar lalu coba lagi."
    if status == 404 or "NotFound" in name:
        return "Layanan AI tidak ditemukan. Coba lagi nanti."
    if "Timeout" in name or "timed out" in text.lower():
        return "AI terlalu lama menjawab. Coba lagi."
    if "Connection" in name or "connect" in text.lower():
        return "Tidak bisa menghubungi layanan AI. Periksa koneksi internet."
    if "BadRequest" in name or status == 400:
        return "Permintaan tidak bisa diproses. Coba lagi."
    return "AI gagal menjawab. Coba lagi."


def stream_chat(
    system: str,
    messages: list[dict],
    max_tokens: int = MAX_TOKENS["chat"],
    temperature: float = 0.7,
) -> Iterator[str]:
    cfg = config()
    if not cfg.ready:
        raise LLMError("Layanan AI belum siap. Hubungi pengelola aplikasi.")
    payload: list[dict] = [{"role": "system", "content": system}] + messages
    try:
        stream = _client().chat.completions.create(
            model=cfg.model,
            messages=payload,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
    except LLMError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise LLMError(_friendly(exc)) from exc


def complete(
    system: str,
    prompt: str,
    max_tokens: int = MAX_TOKENS["chat"],
    temperature: float = 0.7,
) -> str:
    return "".join(
        stream_chat(
            system,
            [{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
    )


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def parse_json(raw: str) -> Any:
    text = raw.strip()
    match = _JSON_BLOCK.search(text)
    if match:
        text = match.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("tidak ada objek JSON pada balasan")
    return json.loads(text[start : end + 1])


def json_call(
    system: str,
    prompt: str,
    schema: type[BaseModel],
    max_tokens: int,
    temperature: float = 0.2,
) -> BaseModel:
    messages: list[dict] = [{"role": "user", "content": prompt}]
    last_error = ""
    for _attempt in range(2):
        raw = "".join(stream_chat(system, messages, max_tokens, temperature))
        try:
            return schema.model_validate(parse_json(raw))
        except (ValueError, ValidationError) as exc:
            last_error = str(exc)
            messages.extend(
                [
                    {"role": "assistant", "content": raw[:3000]},
                    {
                        "role": "user",
                        "content": (
                            "Balasan itu tidak sesuai skema. Kesalahan:\n"
                            f"{last_error[:1200]}\n\n"
                            "Balas ulang HANYA dengan JSON valid sesuai skema."
                        ),
                    },
                ]
            )
    raise LLMError("AI belum bisa memberi jawaban yang sesuai. Coba lagi.")