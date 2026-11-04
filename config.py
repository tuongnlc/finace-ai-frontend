from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import tomllib
from typing import Any
import streamlit as st


LOCAL_SECRETS_FILE = Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"


def _load_local_secrets() -> dict[str, Any]:
    if not LOCAL_SECRETS_FILE.exists():
        return {}

    with LOCAL_SECRETS_FILE.open("rb") as file:
        return tomllib.load(file)


def _load_streamlit_secrets() -> dict[str, Any]:
    try:
        return dict(st.secrets)
    except Exception:
        return {}


def get_secrets() -> dict[str, Any]:
    local_secrets = _load_local_secrets()
    streamlit_secrets = _load_streamlit_secrets()
    return {**local_secrets, **streamlit_secrets}


def get_secret(key: str, default: Any = None) -> Any:
    return get_secrets().get(key, default)


def get_secret_section(section: str) -> dict[str, Any]:
    value = get_secrets().get(section, {})
    return dict(value) if isinstance(value, Mapping) else {}

def get_backend_base_url(default: str = "https://backend-fastapi-7474647713604067.aws.databricksapps.com/") -> str:
    backend_config = get_secret_section("backend")
    return backend_config.get("BACK_END_URL") or backend_config.get("base_url") or default
