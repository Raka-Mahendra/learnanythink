from __future__ import annotations

import pytest

from services import llm


@pytest.fixture()
def clean_env(monkeypatch):
    for name in (
        "TH_API_KEY",
        "TH_BASE_URL",
        "TH_MODEL",
        "TOKEN_HARBOR_API_KEY",
        "TOKEN_HARBOR_BASE_URL",
        "TOKEN_HARBOR_MODEL",
        "LA_API_KEY",
        "LA_BASE_URL",
        "LA_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(llm, "_secret_value", lambda name: "")
    yield monkeypatch


def test_defaults_point_to_token_harbor(clean_env):
    cfg = llm.config()
    assert cfg.base_url == "https://tokenharbor.ai/v1"
    assert cfg.model == "deepseek-v4.1-flash:free"
    assert cfg.ready is False


def test_environment_configuration(clean_env):
    clean_env.setenv("TOKEN_HARBOR_API_KEY", "thk_test")
    clean_env.setenv("TOKEN_HARBOR_MODEL", "model-lain")
    cfg = llm.config()
    assert cfg.api_key == "thk_test"
    assert cfg.model == "model-lain"
    assert cfg.ready is True


def test_primary_names_win(clean_env):
    clean_env.setenv("TH_API_KEY", "utama")
    clean_env.setenv("TOKEN_HARBOR_API_KEY", "cadangan")
    assert llm.config().api_key == "utama"


def test_no_key_means_not_ready(clean_env):
    cfg = llm.config()
    assert cfg.ready is False