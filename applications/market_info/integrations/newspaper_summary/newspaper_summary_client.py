from __future__ import annotations

from datetime import date
from typing import Optional
import requests
import streamlit as st
from applications.schemas.newspaper_summary import DeleteNewspaperSumResponse, GetNewspaperSummaryResponse
from config import get_backend_base_url


@st.cache_resource(show_spinner=False)
def _get_http_session() -> requests.Session:
    """Dùng chung 1 HTTP session để tái sử dụng connection pool giữa các lần rerun."""
    return requests.Session()


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
            f"{self.base_url}/newspaper-summary/",
            params={
                "min_date": min_date,
                "max_date": max_date,
            },
            headers={
                "accept": "*/*",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return [
            GetNewspaperSummaryResponse.model_validate(item)
            for item in response.json()
        ]

    def delete_summaries(self, summary_id: str) -> None:
        response = _get_http_session().delete(
            f"{self.base_url}/newspaper-summary/{summary_id}",
            headers={
                "accept": "*/*",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return None

    def add_to_favorite(self, summary_id: str) -> None:
        response = _get_http_session().put(
            f"{self.base_url}/newspaper-summary/{summary_id}",
            params={
                "is_favorite": 1,
            },
            headers={
                "accept": "*/*",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return None