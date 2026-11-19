"""
Client gọi trực tiếp Databricks Lakebase Data API (PostgREST) để quản lý
Conversation, thay vì đi qua backend FastAPI.

Dữ liệu đọc/ghi trên bảng ``ai_chatbot.conversation``.
Xác thực bằng OAuth M2M (service principal).
"""

from __future__ import annotations

from datetime import date
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
_TABLE = "conversation"

_SELECT_COLUMNS = (
    "id,space_id,user_id,created_timestamp,status,created_at,session_id,title"
)


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
