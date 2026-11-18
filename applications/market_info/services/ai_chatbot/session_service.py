from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from applications.market_info.integrations.ai_chatbot.session_client import (
    ChatSessionClient,
    CreateChatSessionRequest,
)


class ChatSession(BaseModel):
    id: UUID
    created_timestamp: Optional[int] = None
    conversation_id: Optional[UUID] = None


class ChatSessionService:
    def __init__(self, client=None):
        if client is None:
            client = ChatSessionClient()
        self.client = client

    def create_sessions(
        self,
        created_timestamp: int,
        conversation_id: UUID,
    ) -> ChatSession:
        response = self.client.create_sessions(
            CreateChatSessionRequest(
                created_timestamp=created_timestamp,
                conversation_id=conversation_id,
            )
        )

        return ChatSession(
            id=response.id,
            created_timestamp=response.created_timestamp,
            conversation_id=response.conversation_id,
        )

    def get_sessions(self, session_id: UUID) -> ChatSession:
        response = self.client.get_sessions(session_id)

        return ChatSession(
            id=response.id,
            created_timestamp=response.created_timestamp,
            conversation_id=response.conversation_id,
        )

    def update_sessions(
        self,
        session_id: UUID,
        updates: dict[str, Any],
    ) -> ChatSession:
        response = self.client.update_sessions(session_id, updates)

        return ChatSession(
            id=response.id,
            created_timestamp=response.created_timestamp,
            conversation_id=response.conversation_id,
        )

    def delete_sessions(self, session_id: UUID) -> None:
        return self.client.delete_sessions(session_id)
