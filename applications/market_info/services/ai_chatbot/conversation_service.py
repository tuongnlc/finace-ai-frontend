from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from applications.market_info.integrations.ai_chatbot.conversation_client import (
    ConversationClient,
    CreateConversationRequest,
)


class Conversation(BaseModel):
    id: UUID
    space_id: Optional[str] = None
    user_id: Optional[str] = None
    created_timestamp: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[date] = None
    session_id: Optional[UUID] = None
    title: Optional[str] = None


class ConversationService:
    def __init__(self, client=None):
        if client is None:
            client = ConversationClient()
        self.client = client

    def create_conversation(
        self,
        conversation_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        space_id: Optional[str] = None,
        created_timestamp: Optional[int] = None,
        status: Optional[str] = None,
        created_at: Optional[date] = None,
        session_id: Optional[UUID] = None,
        title: Optional[str] = None,
    ) -> Conversation:
        response = self.client.create_conversation(
            CreateConversationRequest(
                id=conversation_id,
                user_id=user_id,
                space_id=space_id,
                created_timestamp=created_timestamp,
                status=status,
                created_at=created_at,
                session_id=session_id,
                title=title,
            )
        )

        return Conversation(
            id=response.id,
            space_id=response.space_id,
            user_id=response.user_id,
            created_timestamp=response.created_timestamp,
            status=response.status,
            created_at=response.created_at,
            session_id=response.session_id,
            title=response.title,
        )

    def get_conversation(self, conversation_id: UUID) -> Conversation:
        response = self.client.get_conversation(conversation_id)

        return Conversation(
            id=response.id,
            space_id=response.space_id,
            user_id=response.user_id,
            created_timestamp=response.created_timestamp,
            status=response.status,
            created_at=response.created_at,
            session_id=response.session_id,
            title=response.title,
        )

    def list_conversations(self, user_id: str) -> list[Conversation]:
        responses = self.client.list_conversations(user_id)

        return [
            Conversation(
                id=response.id,
                space_id=response.space_id,
                user_id=response.user_id,
                created_timestamp=response.created_timestamp,
                status=response.status,
                created_at=response.created_at,
                session_id=response.session_id,
                title=response.title,
            )
            for response in responses
        ]

    def update_conversation(
        self,
        conversation_id: UUID,
        updates: dict[str, Any],
    ) -> Conversation:
        response = self.client.update_conversation(conversation_id, updates)

        return Conversation(
            id=response.id,
            space_id=response.space_id,
            user_id=response.user_id,
            created_timestamp=response.created_timestamp,
            status=response.status,
            created_at=response.created_at,
            session_id=response.session_id,
            title=response.title,
        )

    def delete_conversation(self, conversation_id: UUID) -> None:
        return self.client.delete_conversation(conversation_id)
