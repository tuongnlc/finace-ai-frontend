"""
Client gọi trực tiếp Databricks Lakebase Data API (PostgREST) để quản lý
Chat Session, thay vì đi qua backend FastAPI.

Dữ liệu đọc/ghi trên bảng ``ai_chatbot.chat_session``.
Xác thực bằng OAuth M2M (service principal).
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

import requests
from pydantic import BaseModel

from applications.market_info.integrations.databricks_lakebase import (
    databricks_auth,
    get_http_session,
    lakebase_api_base,
)


# ---------------------------------------------------------------------------
# Databricks (Lakebase Data API) configuration
# ---------------------------------------------------------------------------
_SCHEMA = "ai_chatbot"
_TABLE = "chat_session"

_SELECT_COLUMNS = "id,created_timestamp,conversation_id"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CreateChatSessionRequest(BaseModel):
    id: Optional[UUID] = None
    created_timestamp: int
    conversation_id: UUID


class GetChatSessionResponse(BaseModel):
    id: UUID
    created_timestamp: Optional[int] = None
    conversation_id: Optional[UUID] = None


class ChatSessionClient:
    """
    Client for Chat Session API

    Quản lý Chat Session trực tiếp qua Databricks Lakebase Data API
    (schema ``ai_chatbot``, bảng ``chat_session``).
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
        url = f"{lakebase_api_base().rstrip('/')}/{_SCHEMA}/{_TABLE}"
        headers = {**databricks_auth(), "Accept": "application/json"}
        if prefer:
            headers["Prefer"] = prefer

        response = get_http_session().request(
            method,
            url,
            params=params,
            json=json_body,
            headers=headers,
            timeout=self.timeout,
        )
        if not response.ok:
            # raise_for_status() che mất body lỗi của PostgREST, khiến việc debug
            # các lỗi 404 (bảng/schema chưa được expose) rất khó. Nêu rõ body.
            raise requests.HTTPError(
                f"{method} {url} -> {response.status_code} {response.reason}: "
                f"{response.text}",
                response=response,
            )
        return response

    # -- operations -------------------------------------------------------
    def create_sessions(
        self,
        session: CreateChatSessionRequest,
    ) -> GetChatSessionResponse:
        response = self._request(
            "POST",
            json_body=session.model_dump(mode="json", exclude_none=True),
            prefer="return=representation",
        )
        rows = response.json()
        return GetChatSessionResponse.model_validate(rows[0])

    def get_sessions(self, session_id: UUID) -> GetChatSessionResponse:
        response = self._request(
            "GET",
            params=[
                ("id", f"eq.{session_id}"),
                ("select", _SELECT_COLUMNS),
            ],
        )
        rows = response.json()
        if not rows:
            raise ValueError(f"Không tìm thấy Chat Session: {session_id}")
        return GetChatSessionResponse.model_validate(rows[0])

    def update_sessions(
        self,
        session_id: UUID,
        updates: dict[str, Any],
    ) -> GetChatSessionResponse:
        response = self._request(
            "PATCH",
            params=[("id", f"eq.{session_id}")],
            json_body=updates,
            prefer="return=representation",
        )
        rows = response.json()
        if not rows:
            raise ValueError(f"Không tìm thấy Chat Session: {session_id}")
        return GetChatSessionResponse.model_validate(rows[0])

    def delete_sessions(self, session_id: UUID) -> None:
        self._request(
            "DELETE",
            params=[("id", f"eq.{session_id}")],
        )
        return None
