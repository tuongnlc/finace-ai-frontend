from __future__ import annotations

from datetime import date
from typing import Optional
import requests
import streamlit as st
from applications.schemas.newspaper_summary import GetNewspaperSummaryResponse
from config import get_backend_base_url


@st.cache_resource(show_spinner=False)
def _get_http_session() -> requests.Session:
    """Dùng chung 1 HTTP session để tái sử dụng connection pool giữa các lần rerun."""
    return requests.Session()


def _auth_headers() -> dict[str, str]:
    """Header gửi kèm khi gọi backend, mang token của user hiện tại (Databricks Apps)."""
    headers = {"accept": "*/*"}
    try:
        token = st.context.headers.get("X-Forwarded-Access-Token")
    except Exception:
        token = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class NewspaperSummaryClient:
    """
        Client for Newspaper Summary API

        List newspaper summaries within a date range
    """

    def __init__(self, base_url: str | None = None, timeout: int = 30) -> None:
        self.base_url = (base_url or get_backend_base_url()).rstrip("/")
        self.timeout = timeout

    def list_summaries(
        self,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None,
    ) -> list[GetNewspaperSummaryResponse]:
        response = _get_http_session().get(
            f"{self.base_url}/newspaper-topic-tagging/",
            params={
                "min_date": min_date,
                "max_date": max_date,
            },
            headers=_auth_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return [
            GetNewspaperSummaryResponse.model_validate(item)
            for item in response.json()
        ]

    def delete_summaries(self, newspaper_url: str) -> None:
        response = _get_http_session().delete(
            f"{self.base_url}/newspaper-topic-tagging/{newspaper_url}",
            headers=_auth_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return None
