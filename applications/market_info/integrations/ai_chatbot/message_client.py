"""
Client gọi trực tiếp Databricks Lakebase Data API (PostgREST) để quản lý
Message, thay vì đi qua backend FastAPI.

Dữ liệu đọc/ghi trên bảng ``ai_chatbot.messages``.
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
_TABLE = "messages"

_SELECT_COLUMNS = (
    "id,space_id,conversation_id,user_id,created_timestamp,message_url,"
    "status,content,created_at"
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CreateMessageRequest(BaseModel):
    id: Optional[UUID] = None
    space_id: Optional[str] = None
    conversation_id: Optional[UUID] = None
    user_id: Optional[str] = None
    created_timestamp: Optional[int] = None
    message_url: Optional[str] = None
    status: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[date] = None


class GetMessageResponse(BaseModel):
    id: UUID
    space_id: Optional[str] = None
    conversation_id: Optional[UUID] = None
    user_id: Optional[str] = None
    created_timestamp: Optional[int] = None
    message_url: Optional[str] = None
    status: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[date] = None


class MessageClient:
    """
    Client for Message API

    Quản lý Message trực tiếp qua Databricks Lakebase Data API
    (schema ``ai_chatbot``, bảng ``messages``).
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
    def create_message(
        self,
        message: CreateMessageRequest,
    ) -> GetMessageResponse:
        response = self._request(
            "POST",
            json_body=message.model_dump(mode="json", exclude_none=True),
            prefer="return=representation",
        )
        rows = response.json()
        return GetMessageResponse.model_validate(rows[0])

    def get_message(self, message_id: UUID) -> GetMessageResponse:
        response = self._request(
            "GET",
            params=[
                ("id", f"eq.{message_id}"),
                ("select", _SELECT_COLUMNS),
            ],
        )
        rows = response.json()
        if not rows:
            raise ValueError(f"Không tìm thấy Message: {message_id}")
        return GetMessageResponse.model_validate(rows[0])

    def list_messages(
        self, conversation_id: UUID
    ) -> list[GetMessageResponse]:
        response = self._request(
            "GET",
            params=[
                ("conversation_id", f"eq.{conversation_id}"),
                ("select", _SELECT_COLUMNS),
                ("order", "created_timestamp.asc"),
            ],
        )
        return [
            GetMessageResponse.model_validate(row)
            for row in response.json()
        ]

    def update_message(
        self,
        message_id: UUID,
        updates: dict[str, Any],
    ) -> GetMessageResponse:
        response = self._request(
            "PATCH",
            params=[("id", f"eq.{message_id}")],
            json_body=updates,
            prefer="return=representation",
        )
        rows = response.json()
        if not rows:
            raise ValueError(f"Không tìm thấy Message: {message_id}")
        return GetMessageResponse.model_validate(rows[0])

    def delete_message(self, message_id: UUID) -> None:
        self._request(
            "DELETE",
            params=[("id", f"eq.{message_id}")],
        )
        return None
