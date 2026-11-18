from __future__ import annotations

import streamlit as st

DEFAULT_GREETING = "Chào bạn! Tôi có thể giúp gì cho bạn?"
DEFAULT_TITLE = "🤖 Trợ lý AI"

VIEWPORT_SCRIPT = """
<script>
(() => {
    // Yêu cầu trình duyệt co lại layout viewport khi bàn phím ảo mở ra
    // (Android Chrome). Nếu không, bàn phím sẽ đè lên các phần tử position:fixed.
    const meta = document.querySelector('meta[name="viewport"]');
    if (meta) {
        const content = meta.getAttribute("content") || "";
        if (!content.includes("interactive-widget")) {
            meta.setAttribute("content", content + ", interactive-widget=resizes-content");
        }
    }

    let rafId = null;
    const updateViewport = () => {
        if (rafId) cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(() => {
            const vv = window.visualViewport;
            const height = vv?.height || window.innerHeight;
            const top = vv?.offsetTop || 0;
            document.documentElement.style.setProperty(
                "--floating-chat-viewport-height",
                `${height}px`
            );
            document.documentElement.style.setProperty(
                "--floating-chat-viewport-top",
                `${top}px`
            );
        });
    };

    updateViewport();
    if (!window.__floatingChatInited) {
        window.__floatingChatInited = true;
        window.visualViewport?.addEventListener("resize", updateViewport);
        window.visualViewport?.addEventListener("scroll", updateViewport);
        window.addEventListener("resize", updateViewport);
        window.addEventListener("orientationchange", updateViewport);
        // Khi ô nhập được focus (bàn phím mở), cập nhật lại chiều cao khung chat
        // vì một số trình duyệt cập nhật visualViewport trễ một chút.
        document.addEventListener("focusin", (e) => {
            if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) {
                setTimeout(updateViewport, 100);
                setTimeout(updateViewport, 350);
            }
        });
    }
})();
</script>
"""

# Popover trong Streamlit render dạng: stPopover > div > (wrapper) > button[stPopoverButton].
# Nên phải style theo data-testid="stPopoverButton", không dùng selector `> button`.
STYLES = """
<style>
/* Ghim nút chat vào góc phải dưới màn hình.
   Lưu ý: container stPopover mặc định có width:100%, nếu không reset width/left
   thì khối sẽ trải hết chiều ngang và nút bị đẩy về tận mép trái. */
div[data-testid="stPopover"] {
    position: fixed;
    bottom: 24px;
    right: 24px;
    left: auto !important;
    width: auto !important;
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

/* Khung chat bung ra (desktop) */
div[data-testid="stPopoverBody"] {
    width: min(380px, calc(100vw - 32px)) !important;
    max-width: calc(100vw - 32px) !important;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

/* Mobile: chuyển popover thành khung chat toàn màn hình. */
@media (max-width: 640px) {
    div[data-testid="stPopoverBody"] {
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: var(--floating-chat-viewport-height, 100dvh) !important;
        max-height: none !important;
        max-width: none !important;
        min-width: 0 !important;
        transform: none !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
        border-radius: 0 !important;
        padding:
            calc(12px + env(safe-area-inset-top, 0px))
            12px
            calc(12px + env(safe-area-inset-bottom, 0px)) !important;
        z-index: 2147483000 !important;
    }

    /* Cấu trúc DOM thật của Streamlit popover:
       stPopoverBody
         > [data-testid="stVerticalBlock"]            (container chính, cần là flex)
           > stElementContainer (title)
           > [data-testid="stLayoutWrapper"]           ← flex item, cần flex:1
             > .st-key-floating_chat_history          (class key nằm ở đây)
           > form

       Lưu ý: class "st-key-..." nằm trên stVerticalBlock BÊN TRONG stLayoutWrapper,
       không phải trên stLayoutWrapper. Nên phải dùng :has() để target đúng wrapper. */

    /* Container chính (con trực tiếp của popover body) là flex column. */
    div[data-testid="stPopoverBody"] > [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
        width: 100% !important;
        height: 100% !important;
        min-height: 0 !important;
        overflow: hidden !important;
    }

    /* Wrapper của khối lịch sử chat (st.container) - đây mới là flex item
       cần chiếm phần không gian còn trống. height:0 + flex:1 1 0 để bỏ qua
       inline style height:320px và co giãn theo không gian còn lại. */
    div[data-testid="stPopoverBody"] [data-testid="stLayoutWrapper"]:has(.FLOATING_CHAT_HISTORY_KEY) {
        flex: 1 1 0 !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: none !important;
        overflow: hidden !important;
    }

    /* Khối stVerticalBlock bên trong lấp đầy chiều cao của wrapper. */
    div[data-testid="stPopoverBody"] .FLOATING_CHAT_HISTORY_KEY {
        height: 100% !important;
        min-height: 0 !important;
        max-height: none !important;
        overflow-y: auto !important;
        overscroll-behavior: contain;
    }

    /* Form (ô nhập + nút Gửi) cố định ở dưới, không co lại. */
    div[data-testid="stPopoverBody"] form {
        flex: 0 0 auto !important;
        margin-top: 8px !important;
    }

    /* Ô nhập liệu phải >= 16px, nếu không iOS Safari sẽ tự zoom trang
       (làm khung chat phình to và che mất nội dung phía trên). */
    div[data-testid="stPopoverBody"] input,
    div[data-testid="stPopoverBody"] textarea {
        font-size: 16px !important;
    }
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
        # placeholder: str = "Nhập câu hỏi...",
        key: str = "floating_chat",
    ):
        self.title = title
        # self.placeholder = placeholder
        self.key = key

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
                for message in self._messages():
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
                        key=self._input_key,
                    )
                with button_column:
                    st.form_submit_button("Gửi", on_click=self._on_submit)

    def _on_submit(self) -> None:
        user_input = (st.session_state.get(self._input_key) or "").strip()
        if not user_input:
            return
        self._append_exchange(user_input)
        st.session_state[self._input_key] = ""

    @property
    def _input_key(self) -> str:
        return f"{self.key}__input"

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
