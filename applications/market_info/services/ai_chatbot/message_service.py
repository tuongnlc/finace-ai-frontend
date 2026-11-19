from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from applications.market_info.integrations.ai_chatbot.message_client import (
    CreateMessageRequest,
    MessageClient,
)


class Message(BaseModel):
    id: UUID
    space_id: Optional[str] = None
    conversation_id: Optional[UUID] = None
    user_id: Optional[str] = None
    created_timestamp: Optional[int] = None
    message_url: Optional[str] = None
    status: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[date] = None


class MessageService:
    def __init__(self, client=None):
        if client is None:
            client = MessageClient()
        self.client = client

    def create_message(
        self,
        message_id: Optional[UUID] = None,
        space_id: Optional[str] = None,
        conversation_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        created_timestamp: Optional[int] = None,
        message_url: Optional[str] = None,
        status: Optional[str] = None,
        content: Optional[str] = None,
        created_at: Optional[date] = None,
    ) -> Message:
        response = self.client.create_message(
            CreateMessageRequest(
                id=message_id,
                space_id=space_id,
                conversation_id=conversation_id,
                user_id=user_id,
                created_timestamp=created_timestamp,
                message_url=message_url,
                status=status,
                content=content,
                created_at=created_at,
            )
        )

        return Message(
            id=response.id,
            space_id=response.space_id,
            conversation_id=response.conversation_id,
            user_id=response.user_id,
            created_timestamp=response.created_timestamp,
            message_url=response.message_url,
            status=response.status,
            content=response.content,
            created_at=response.created_at,
        )

    def get_message(self, message_id: UUID) -> Message:
        response = self.client.get_message(message_id)

        return Message(
            id=response.id,
            space_id=response.space_id,
            conversation_id=response.conversation_id,
            user_id=response.user_id,
            created_timestamp=response.created_timestamp,
            message_url=response.message_url,
            status=response.status,
            content=response.content,
            created_at=response.created_at,
        )

    def list_messages(self, conversation_id: UUID) -> list[Message]:
        responses = self.client.list_messages(conversation_id)

        return [
            Message(
                id=response.id,
                space_id=response.space_id,
                conversation_id=response.conversation_id,
                user_id=response.user_id,
                created_timestamp=response.created_timestamp,
                message_url=response.message_url,
                status=response.status,
                content=response.content,
                created_at=response.created_at,
            )
            for response in responses
        ]

    def update_message(
        self,
        message_id: UUID,
        updates: dict[str, Any],
    ) -> Message:
        response = self.client.update_message(message_id, updates)

        return Message(
            id=response.id,
            space_id=response.space_id,
            conversation_id=response.conversation_id,
            user_id=response.user_id,
            created_timestamp=response.created_timestamp,
            message_url=response.message_url,
            status=response.status,
            content=response.content,
            created_at=response.created_at,
        )

    def delete_message(self, message_id: UUID) -> None:
        return self.client.delete_message(message_id)
