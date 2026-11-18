"""
Client gọi trực tiếp Databricks Lakebase Data API (PostgREST) để quản lý
Conversation, thay vì đi qua backend FastAPI.

Dữ liệu đọc/ghi trên bảng ``ai_chatbot.conversation``.
Xác thực bằng OAuth M2M (service principal).
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any, Optional
from uuid import UUID

import requests
from databricks.sdk import WorkspaceClient
from pydantic import BaseModel

from config import get_secret


# ---------------------------------------------------------------------------
# Databricks (Lakebase Data API) configuration
# ---------------------------------------------------------------------------
_SCHEMA = "ai_chatbot"
_TABLE = "conversation"

# Base URL mặc định của Lakebase Data API (có thể override qua biến môi trường
# hoặc secrets.toml với key DATABRICKS_LAKEBASE_API_BASE).
_DEFAULT_LAKEBASE_API_BASE = (
    "https://ep-ancient-pine-d8w8ldyd.database.us-east-2.cloud.databricks.com"
    "/api/2.0/workspace/7474647713604067/rest/databricks_postgres"
)

_SELECT_COLUMNS = (
    "id,space_id,user_id,created_timestamp,status,created_at,session_id,title"
)

_workspace_client: WorkspaceClient | None = None
_http_session: requests.Session | None = None


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CreateConversationRequest(BaseModel):
    id: Optional[UUID] = None
    user_id: Optional[str] = None
    space_id: Optional[str] = None
    created_timestamp: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[date] = None
    session_id: Optional[UUID] = None
    title: Optional[str] = None


class GetConversationResponse(BaseModel):
    id: UUID
    space_id: Optional[str] = None
    user_id: Optional[str] = None
    created_timestamp: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[date] = None
    session_id: Optional[UUID] = None
    title: Optional[str] = None


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


class ConversationClient:
    """
    Client for Conversation API

    Quản lý Conversation trực tiếp qua Databricks Lakebase Data API
    (schema ``ai_chatbot``, bảng ``conversation``).
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
    def create_conversation(
        self,
        conversation: CreateConversationRequest,
    ) -> GetConversationResponse:
        response = self._request(
            "POST",
            json_body=conversation.model_dump(mode="json", exclude_none=True),
            prefer="return=representation",
        )
        rows = response.json()
        return GetConversationResponse.model_validate(rows[0])

    def get_conversation(self, conversation_id: UUID) -> GetConversationResponse:
        response = self._request(
            "GET",
            params=[
                ("id", f"eq.{conversation_id}"),
                ("select", _SELECT_COLUMNS),
            ],
        )
        rows = response.json()
        if not rows:
            raise ValueError(f"Không tìm thấy Conversation: {conversation_id}")
        return GetConversationResponse.model_validate(rows[0])

    def list_conversations(self, user_id: str) -> list[GetConversationResponse]:
        response = self._request(
            "GET",
            params=[
                ("user_id", f"eq.{user_id}"),
                ("select", _SELECT_COLUMNS),
                ("order", "created_timestamp.desc"),
            ],
        )
        return [
            GetConversationResponse.model_validate(row)
            for row in response.json()
        ]

    def update_conversation(
        self,
        conversation_id: UUID,
        updates: dict[str, Any],
    ) -> GetConversationResponse:
        response = self._request(
            "PATCH",
            params=[("id", f"eq.{conversation_id}")],
            json_body=updates,
            prefer="return=representation",
        )
        rows = response.json()
        if not rows:
            raise ValueError(f"Không tìm thấy Conversation: {conversation_id}")
        return GetConversationResponse.model_validate(rows[0])

    def delete_conversation(self, conversation_id: UUID) -> None:
        self._request(
            "DELETE",
            params=[("id", f"eq.{conversation_id}")],
        )
        return None
