from __future__ import annotations

import streamlit as st

DEFAULT_GREETING = "Chào bạn! Tôi có thể giúp gì cho bạn?"
DEFAULT_TITLE = "🤖 Trợ lý AI"

# Popover trong Streamlit render dạng: stPopover > div > (wrapper) > button[stPopoverButton].
# Nên phải style theo data-testid="stPopoverButton", không dùng selector `> button`.
STYLES = """
<style>
/* Ghim nút chat vào góc phải dưới màn hình */
div[data-testid="stPopover"] {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 9999;
}

/* Nút tròn nổi bật */
div[data-testid="stPopover"] [data-testid="stPopoverButton"] {
    width: 60px !important;
    height: 60px !important;
    min-height: 60px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    background-color: #FF4B4B !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    font-size: 24px !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s ease;
}

div[data-testid="stPopover"] [data-testid="stPopoverButton"]:hover {
    transform: scale(1.08);
    background-color: #ff3333 !important;
    color: #FFFFFF !important;
}

/* Ẩn mũi tên mặc định của popover */
div[data-testid="stPopover"] [data-testid="stPopoverButton"] svg {
    display: none !important;
}

/* Khung chat bung ra */
div[data-testid="stPopoverBody"] {
    width: 380px !important;
    max-width: 90vw !important;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}
</style>
"""


class FloatingChat:
    """Nút chat nổi ở góc phải dưới, dùng chung cho toàn app.

    Cách dùng: gọi ``FloatingChat().render()`` ở entrypoint (app.py) hoặc trong page.
    """

    def __init__(
        self,
        title: str = DEFAULT_TITLE,
        placeholder: str = "Nhập câu hỏi...",
        key: str = "floating_chat",
    ):
        self.title = title
        self.placeholder = placeholder
        self.key = key

    def render(self) -> None:
        st.markdown(STYLES, unsafe_allow_html=True)

        with st.popover("💬"):
            st.markdown(f"### {self.title}")

            with st.container(height=320):
                for message in self._messages():
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

            user_input = self._render_input()
            if user_input:
                self._append_exchange(user_input)
                # Rerun để khung chat hiển thị ngay tin nhắn vừa gửi.
                st.rerun()

    def _render_input(self) -> str | None:
        with st.form(key=f"{self.key}__form", clear_on_submit=True):
            text_column, button_column = st.columns([4, 1])
            with text_column:
                text = st.text_input(
                    "Tin nhắn",
                    placeholder=self.placeholder,
                    label_visibility="collapsed",
                )
            with button_column:
                submitted = st.form_submit_button("Gửi")
        return text if submitted and text else None

    @property
    def _messages_key(self) -> str:
        return f"{self.key}__messages"

    def _messages(self) -> list[dict]:
        if self._messages_key not in st.session_state:
            st.session_state[self._messages_key] = [
                {"role": "assistant", "content": DEFAULT_GREETING}
            ]
        return st.session_state[self._messages_key]

    def _append_exchange(self, user_input: str) -> None:
        messages = self._messages()
        messages.append({"role": "user", "content": user_input})
        # TODO: thay bằng logic gọi LLM/backend thực tế ở đây.
        messages.append(
            {
                "role": "assistant",
                "content": f"Bạn vừa hỏi: '{user_input}'. Đây là câu trả lời tự động.",
            }
        )
