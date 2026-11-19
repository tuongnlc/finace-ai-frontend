from __future__ import annotations

import streamlit as st

from components.chat.floating_chat.state import ChatState
from components.chat.floating_chat.styles import STYLES
from components.chat.floating_chat.view import VIEWPORT_SCRIPT

DEFAULT_TITLE = "🤖 Trợ lý AI"


class FloatingChat:
    """Nút chat nổi ở góc phải dưới, dùng chung cho toàn app.

    Cách dùng: gọi ``FloatingChat().render()`` ở entrypoint (app.py) hoặc trong page.
    """

    def __init__(
        self,
        title: str = DEFAULT_TITLE,
        key: str = "floating_chat",
    ):
        self.title = title
        self.key = key
        self.state = ChatState(key=key)

    def render(self) -> None:
        history_class = f"st-key-{self.key}_history"
        styles = STYLES.replace("FLOATING_CHAT_HISTORY_KEY", history_class)
        st.markdown(styles, unsafe_allow_html=True)
        st.html(VIEWPORT_SCRIPT, unsafe_allow_javascript=True)
        self._render_chat()

    @st.fragment
    def _render_chat(self) -> None:
        # Bọc trong fragment: tương tác chat chỉ làm mới riêng khung chat,
        # không chạy lại toàn bộ page (tránh reload cả trang mỗi lần gửi).
        with st.popover("💬"):
            st.markdown(f"### {self.title}")

            with st.container(height=320, key=f"{self.key}_history"):
                for message in self.state.messages():
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

            # Nút Gửi có on_click: callback chạy trước khi render nên khung chat
            # cập nhật ngay trong cùng lần rerun, không cần gọi st.rerun().
            with st.form(key=f"{self.key}__form"):
                text_column, button_column = st.columns([4, 1])
                with text_column:
                    st.text_input(
                        "Tin nhắn",
                        # placeholder=self.placeholder,
                        label_visibility="collapsed",
                        key=self.state.input_key,
                    )
                with button_column:
                    st.form_submit_button("Gửi", on_click=self._on_submit)

    def _on_submit(self) -> None:
        user_input = (st.session_state.get(self.state.input_key) or "").strip()
        if not user_input:
            return
        self.state.ensure_session()
        self.state.append_exchange(user_input)
        st.session_state[self.state.input_key] = ""
