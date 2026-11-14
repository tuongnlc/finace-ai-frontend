"""
Client gọi trực tiếp Databricks Lakebase Data API (PostgREST) để quản lý
Newspaper Summary, thay vì đi qua backend FastAPI.

Dữ liệu đọc/ghi trên bảng ``market_news.newspaper_topic_tagging``.
Xác thực bằng OAuth M2M (service principal).
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any, Optional

import requests
from databricks.sdk import WorkspaceClient

from applications.schemas.newspaper_summary import (
    CreateNewspaperSummaryRequest,
    GetNewspaperSummaryResponse,
)
from config import get_secret


# ---------------------------------------------------------------------------
# Databricks (Lakebase Data API) configuration
# ---------------------------------------------------------------------------
_SCHEMA = "market_news"
_TABLE = "newspaper_topic_tagging"

# Base URL mặc định của Lakebase Data API (có thể override qua biến môi trường
# hoặc secrets.toml với key DATABRICKS_LAKEBASE_API_BASE).
_DEFAULT_LAKEBASE_API_BASE = (
    "https://ep-ancient-pine-d8w8ldyd.database.us-east-2.cloud.databricks.com"
    "/api/2.0/workspace/7474647713604067/rest/databricks_postgres"
)

_SELECT_COLUMNS = (
    "newspaper_title,newspaper_url,publish_date,newspaper_content,"
    "stocks_mention,main_topic,person_mention,newspaper_summary,"
    "sentiment_analysis"
)

_workspace_client: WorkspaceClient | None = None
_http_session: requests.Session | None = None


def _setting(name: str) -> str | None:
    """Đọc cấu hình Databricks: ưu tiên biến môi trường, fallback secrets.toml."""
    return os.environ.get(name) or get_secret(name)


def _require(name: str, default: str | None = None) -> str:
    value = _setting(name) or default
    if not value:
        raise RuntimeError(
            f"Thiếu cấu hình '{name}'. Khai báo trong biến môi trường "
            f"hoặc .streamlit/secrets.toml."
        )
    return value


def _get_workspace_client() -> WorkspaceClient:
    """Khởi tạo WorkspaceClient dùng chung để lấy token OAuth M2M."""
    global _workspace_client
    if _workspace_client is None:
        _workspace_client = WorkspaceClient(
            host=_require("DATABRICKS_HOST"),
            client_id=_require("DATABRICKS_CLIENT_ID"),
            client_secret=_require("DATABRICKS_CLIENT_SECRET"),
            auth_type="oauth-m2m",
        )
    return _workspace_client


def _databricks_auth() -> dict[str, str]:
    """Header Authorization (OAuth M2M) để gọi Lakebase Data API."""
    return _get_workspace_client().config.authenticate()


def _get_http_session() -> requests.Session:
    """Dùng chung 1 HTTP session để tái sử dụng connection pool."""
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
    return _http_session


class NewspaperSummaryClient:
    """
    Client for Newspaper Summary API

    Quản lý Newspaper Summary trực tiếp qua Databricks Lakebase Data API
    (schema ``market_news``, bảng ``newspaper_topic_tagging``).
    """

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    # -- internal ---------------------------------------------------------
    def _request(
        self,
        method: str,
        *,
        params: list[tuple[str, str]] | None = None,
        json_body: Any | None = None,
        prefer: str | None = None,
    ) -> requests.Response:
        base = _require(
            "DATABRICKS_LAKEBASE_API_BASE", default=_DEFAULT_LAKEBASE_API_BASE
        )
        url = f"{base.rstrip('/')}/{_SCHEMA}/{_TABLE}"
        headers = {**_databricks_auth(), "Accept": "application/json"}
        if prefer:
            headers["Prefer"] = prefer

        response = _get_http_session().request(
            method,
            url,
            params=params,
            json=json_body,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    # -- operations -------------------------------------------------------
    def list_summaries(
        self,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None,
    ) -> list[GetNewspaperSummaryResponse]:
        params: list[tuple[str, str]] = []
        if min_date is not None:
            params.append(("publish_date", f"gte.{min_date.isoformat()}"))
        if max_date is not None:
            params.append(("publish_date", f"lte.{max_date.isoformat()}"))
        params.append(("select", _SELECT_COLUMNS))
        params.append(("order", "publish_date.desc"))

        response = self._request("GET", params=params)
        return [
            GetNewspaperSummaryResponse.model_validate(row)
            for row in response.json()
        ]

    def create_summaries(
        self,
        summary: CreateNewspaperSummaryRequest,
    ) -> GetNewspaperSummaryResponse:
        response = self._request(
            "POST",
            json_body=summary.model_dump(mode="json"),
            prefer="return=representation",
        )
        rows = response.json()
        return GetNewspaperSummaryResponse.model_validate(rows[0])

    def update_summaries(
        self,
        newspaper_url: str,
        updates: dict[str, Any],
    ) -> GetNewspaperSummaryResponse:
        response = self._request(
            "PATCH",
            params=[("newspaper_url", f"eq.{newspaper_url}")],
            json_body=updates,
            prefer="return=representation",
        )
        rows = response.json()
        if not rows:
            raise ValueError(f"Không tìm thấy Newspaper Summary: {newspaper_url}")
        return GetNewspaperSummaryResponse.model_validate(rows[0])

    def delete_summaries(self, newspaper_url: str) -> None:
        self._request(
            "DELETE",
            params=[("newspaper_url", f"eq.{newspaper_url}")],
        )
        return None
