from __future__ import annotations

import time
from uuid import UUID, uuid4

import streamlit as st

from applications.market_info.integrations.ai_chatbot.call_llm import LLMClient
from applications.market_info.services.ai_chatbot.conversation_service import (
    ConversationService,
)
from applications.market_info.services.ai_chatbot.message_service import (
    MessageService,
)
from applications.market_info.services.ai_chatbot.session_service import (
    ChatSessionService,
)

DEFAULT_GREETING = "Chào bạn! Tôi có thể giúp gì cho bạn?"


@st.cache_resource
def _get_session_service() -> ChatSessionService:
    """Service tạo Chat Session, cache lại để tái sử dụng kết nối."""
    return ChatSessionService()


@st.cache_resource
def _get_conversation_service() -> ConversationService:
    """Service tạo Conversation, cache lại để tái sử dụng kết nối."""
    return ConversationService()


@st.cache_resource
def _get_message_service() -> MessageService:
    """Service tạo Message, cache lại để tái sử dụng kết nối."""
    return MessageService()


@st.cache_resource
def _get_llm_client() -> LLMClient:
    """Client gọi LLM, cache lại để tái sử dụng kết nối tới AI Gateway."""
    return LLMClient()


@st.cache_data(ttl=300, show_spinner=False)
def _get_prompt_template():
    """Tải prompt từ MLflow một lần rồi cache, tránh gọi lại mỗi tin nhắn."""
    return _get_llm_client().load_prompt_template()


class ChatState:
    """Quản lý state của khung chat: session, conversation và tin nhắn."""

    def __init__(
        self,
        key: str = "floating_chat",
        greeting: str = DEFAULT_GREETING,
    ):
        self.key = key
        self.greeting = greeting

    @property
    def input_key(self) -> str:
        return f"{self.key}__input"

    @property
    def messages_key(self) -> str:
        return f"{self.key}__messages"

    @property
    def session_id_key(self) -> str:
        return f"{self.key}__session_id"

    @property
    def conversation_id_key(self) -> str:
        return f"{self.key}__conversation_id"

    @property
    def conversation_id(self) -> UUID | None:
        return st.session_state.get(self.conversation_id_key)

    def messages(self) -> list[dict]:
        if self.messages_key not in st.session_state:
            st.session_state[self.messages_key] = [
                {"role": "assistant", "content": self.greeting}
            ]
        return st.session_state[self.messages_key]

    def ensure_session(self) -> None:
        # Lần chat đầu tiên trong phiên tạo mới cả Conversation và Chat Session.
        # Chỉ sinh session_id và conversation_id MỘT lần rồi dùng chung cho cả
        # hai service (hai bảng tham chiếu chéo: session.conversation_id và
        # conversation.session_id); các tin nhắn sau dùng lại cho tới khi user
        # refresh page.
        if self.session_id_key in st.session_state:
            return

        created_timestamp = int(time.time() * 1000)
        session_id = uuid4()
        conversation_id = uuid4()

        _get_conversation_service().create_conversation(
            conversation_id=conversation_id,
            session_id=session_id,
            created_timestamp=created_timestamp,
        )
        _get_session_service().create_sessions(
            session_id=session_id,
            created_timestamp=created_timestamp,
            conversation_id=conversation_id,
        )

        st.session_state[self.session_id_key] = session_id
        st.session_state[self.conversation_id_key] = conversation_id

    def append_exchange(self, user_input: str) -> None:
        messages = self.messages()
        messages.append({"role": "user", "content": user_input})
        self._save_user_message(user_input)

        # Gọi LLM với prompt đã cache ở tầng UI (client + template), chưa lưu
        # câu trả lời vào database.
        answer = _get_llm_client().complete(
            question=user_input,
            prompt_template=_get_prompt_template(),
        )
        messages.append({"role": "assistant", "content": answer})

    def _save_user_message(self, content: str) -> None:
        # Mỗi tin nhắn của user là một row trong bảng ai_chatbot.messages, liên kết
        # với conversation hiện tại qua conversation_id (một conversation có nhiều
        # message); các tin trong cùng phiên tái sử dụng cùng conversation_id.
        _get_message_service().create_message(
            message_id=uuid4(),
            conversation_id=self.conversation_id,
            created_timestamp=int(time.time() * 1000),
            content=content,
        )
