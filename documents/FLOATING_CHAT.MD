# Floating Chat

Nút chat nổi ở góc phải-dưới màn hình, dùng chung cho toàn app. Khi bấm vào nút,
popover bung ra thành khung chat (desktop: khung nhỏ cạnh nút; mobile: toàn màn hình).

Đường dẫn package: `components/chat/floating_chat/`

## Cấu trúc

```
components/chat/floating_chat/
├── __init__.py         # Export công khai: FloatingChat
├── floating_chat.py    # View + wiring: class FloatingChat
├── state.py            # State: class ChatState (+ 2 service cache)
├── styles.py           # Asset CSS: STYLES
└── view.py             # Asset JS: VIEWPORT_SCRIPT
```

Nguyên tắc tách: **view logic** (dựng UI + xử lý tương tác) nằm ở `floating_chat.py`,
**state** (session/conversation/tin nhắn) nằm ở `state.py`, còn **view assets** (CSS/JS)
tách riêng ra `styles.py` / `view.py`.

| File | Trách nhiệm | Nội dung chính |
|---|---|---|
| `__init__.py` | Điểm vào của package | Re-export `FloatingChat` để `from components.chat.floating_chat import FloatingChat` hoạt động như trước |
| `floating_chat.py` | View + wiring | `FloatingChat`, hằng `DEFAULT_TITLE` |
| `state.py` | State | `ChatState`, hằng `DEFAULT_GREETING`, `_get_session_service`, `_get_conversation_service` |
| `styles.py` | CSS | `STYLES` (chuỗi `<style>...</style>`) |
| `view.py` | JS | `VIEWPORT_SCRIPT` (chuỗi `<script>...</script>`) |

## Luồng hoạt động

1. Entrypoint gọi warm-up kết nối rồi render component:

   ```python
   # app.py
   from components.chat.floating_chat import FloatingChat

   warm_up()                 # lấy token OAuth + mở connection Lakebase ở luồng nền
   FloatingChat().render()   # render sau st.navigation để không phá set_page_config
   ```

2. `FloatingChat.render()`
   - Dựng class CSS động: `st-key-{key}_history`.
   - Thay placeholder `FLOATING_CHAT_HISTORY_KEY` trong `STYLES` bằng class trên rồi
     inject qua `st.markdown(..., unsafe_allow_html=True)`.
   - Inject `VIEWPORT_SCRIPT` qua `st.html(..., unsafe_allow_javascript=True)`.
   - Gọi `_render_chat()`.

3. `FloatingChat._render_chat()` (bọc `@st.fragment`)
   - `st.popover("💬")` chứa tiêu đề + khối lịch sử chat + form nhập.
   - Lịch sử: `st.container(height=320, key=f"{key}_history")` render từng message.
   - Form: `st.text_input` (key = `state.input_key`) + `st.form_submit_button("Gửi",
     on_click=self._on_submit)`.

4. `FloatingChat._on_submit()`
   - Đọc và `strip()` nội dung ô nhập; rỗng thì bỏ qua.
   - `state.ensure_session()` → tạo Conversation + Chat Session ở lần gửi đầu tiên.
   - `state.append_exchange(user_input)` → thêm tin nhắn user + phản hồi.
   - Xóa ô nhập.

## State (`ChatState`)

`ChatState` bọc toàn bộ `st.session_state`, khóa theo `key` (mặc định `floating_chat`)
để có thể render nhiều khung chat độc lập:

| Thuộc tính | Khóa trong `session_state` | Ý nghĩa |
|---|---|---|
| `input_key` | `{key}__input` | Nội dung ô nhập |
| `messages_key` | `{key}__messages` | Danh sách tin nhắn (`role`, `content`) |
| `session_id_key` | `{key}__session_id` | ID Chat Session |
| `conversation_id_key` | `{key}__conversation_id` | ID Conversation |

- `messages()` — khởi tạo danh sách với lời chào `DEFAULT_GREETING` nếu chưa có.
- `ensure_session()` — chỉ sinh `session_id` / `conversation_id` **một lần** rồi dùng
  chung cho cả hai service (hai bảng tham chiếu chéo: `session.conversation_id` và
  `conversation.session_id`); các tin nhắn sau tái sử dụng cho tới khi user refresh page.
- `append_exchange(user_input)` — thêm tin nhắn user, sau đó thêm phản hồi.

Hai service `ChatSessionService` và `ConversationService` được cache bằng
`@st.cache_resource` để tái sử dụng kết nối, không khởi tạo lại mỗi rerun.

## Ghi chú kỹ thuật

- **`@st.fragment`**: tương tác chat chỉ làm mới riêng khung chat, không chạy lại toàn
  bộ page (tránh reload cả trang mỗi lần gửi).
- **`on_click` callback**: chạy *trước* khi render nên khung chat cập nhật ngay trong
  cùng lần rerun, không cần gọi `st.rerun()`. Lưu ý callback không hiển thị được
  spinner, nên hiện tại việc gọi mạng chạy trực tiếp trong callback.
- **`st-popover` / DOM Streamlit**: CSS phải style theo `data-testid="stPopoverButton"`
  (không dùng selector `> button`). Trên mobile, khối lịch sử chat được target qua
  `[data-testid="stLayoutWrapper"]:has(.st-key-{key}_history)` vì class `st-key-...`
  nằm trên `stVerticalBlock` bên trong wrapper, không nằm trên wrapper.
- **Placeholder CSS**: `STYLES` chứa token `FLOATING_CHAT_HISTORY_KEY` được thay bằng
  class key thật lúc runtime. Đổi `key` của `FloatingChat` sẽ tự đổi class tương ứng.
- **Viewport script**: thêm `interactive-widget=resizes-content` vào meta viewport và
  cập nhật biến CSS `--floating-chat-viewport-height` / `--floating-chat-viewport-top`
  từ `visualViewport`, giúp khung chat không bị bàn phím ảo che trên mobile. Có cờ
  `window.__floatingChatInited` để không gắn trùng event listener.
- **`key`**: nên là duy nhất nếu render nhiều khung chat trên cùng page.

## Tích hợp vào app.py

Component được render đúng một lần ở entrypoint `app.py`, đặt **sau** `pg.run()`:

```python
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from applications.market_info.integrations.databricks_lakebase import warm_up
from components.chat.floating_chat import FloatingChat

# Khởi động sớm ngay khi page bắt đầu render: lấy token OAuth + mở sẵn kết nối
# tới Lakebase ở luồng nền, để lần gửi tin đầu tiên không phải chờ token/TLS.
warm_up()

market_news_page = st.Page(
    "pages/market_info/market_news.py",
    title="Tin tức thị trường",
    icon="📰",
)

pg = st.navigation({"THÔNG TIN KINH TẾ": [market_news_page]}, position="sidebar")
pg.run()

# Nút chat nổi dùng chung cho mọi page.
# Render sau pg.run() để không phá vỡ set_page_config() phải là lệnh đầu tiên của page.
FloatingChat().render()
```

Lưu ý:

- `sys.path.insert(...)` để import được package `applications` / `components` khi chạy Streamlit.
- `warm_up()` gọi sớm (best-effort, chạy ở luồng nền) để tin nhắn đầu tiên không phải
  chờ lấy OAuth token và TLS handshake.
- `FloatingChat().render()` **phải** đặt sau `pg.run()`, nếu không sẽ phá `set_page_config()`.
- Có thể truyền tùy chọn: `FloatingChat(title="🤖 Trợ lý AI", key="floating_chat").render()`.

## Ghi vào database khi user gửi tin

Backend là **Databricks Lakebase Data API (PostgREST)**, schema `ai_chatbot`, xác thực
OAuth M2M (service principal). Không đi qua backend FastAPI.

### Khi nào ghi?

- **Tin nhắn đầu tiên** của mỗi phiên: ghi session + conversation + message.
- **Các tin nhắn sau**: chỉ ghi thêm **message** (tin của user), tái sử dụng
  `conversation_id` đã có — `ensure_session()` thoát sớm nên không tạo lại
  session/conversation.

### Chuỗi xử lý khi user bấm "Gửi"

1. `_on_submit()` đọc ô nhập, `strip()`, rỗng thì bỏ qua.
2. `state.ensure_session()` — sinh **một lần** `session_id`, `conversation_id` (UUID4) và
   `created_timestamp` (mili-giây), rồi ghi **2 bản ghi**:

   | Bước | Service (hàm) | Ghi vào bảng | Dữ liệu gửi lên |
   |---|---|---|---|
   | 1 | `ConversationService.create_conversation` | `ai_chatbot.conversation` | `id = conversation_id`, `session_id = session_id`, `created_timestamp` |
   | 2 | `ChatSessionService.create_sessions` | `ai_chatbot.chat_session` | `id = session_id`, `conversation_id = conversation_id`, `created_timestamp` |

   Hai bảng tham chiếu chéo nhau: `conversation.session_id → chat_session.id` và
   `chat_session.conversation_id → conversation.id`. Sau khi ghi xong, hai ID được lưu
   vào `st.session_state` (`{key}__session_id`, `{key}__conversation_id`) để tái sử dụng.

3. `state.append_exchange(user_input)`:
   - Thêm tin nhắn user vào `st.session_state`.
   - `_save_user_message()` ghi 1 row vào `ai_chatbot.messages` (một conversation có
     nhiều message):

     | Service (hàm) | Ghi vào bảng | Dữ liệu gửi lên |
     |---|---|---|
     | `MessageService.create_message` | `ai_chatbot.messages` | `id = uuid4()`, `conversation_id` (tái dùng từ state), `created_timestamp`, `content` (nội dung user nhập) |

   - Thêm phản hồi assistant (placeholder) vào `st.session_state` — chưa persist.
4. Xóa nội dung ô nhập.

### Ghi "như thế nào" (tầng HTTP)

- Mỗi lần ghi = 1 request `POST` tới `{LAKEBASE_API_BASE}/ai_chatbot/{table}` kèm header
  `Prefer: return=representation` (PostgREST trả về chính row vừa tạo để map sang response).
- Chỉ các field khác `None` mới được gửi lên (`model_dump(exclude_none=True)`).
- Header `Authorization` lấy từ `databricks_auth()` (OAuth M2M, token cache ~1 giờ, tự
  làm mới trước khi hết hạn); HTTP dùng chung **một** `requests.Session` để tái sử dụng
  connection pool.
- Nếu PostgREST trả lỗi, client raise `requests.HTTPError` kèm body để dễ debug.
- `ensure_session()` tạo Conversation **trước**, Chat Session **sau**, và không có
  transaction — nên nếu bước 2 lỗi thì có thể để lại một Conversation "mồ côi".

### Bảng `messages`

Mỗi lần user bấm "Gửi" ghi thêm **1 row** vào `ai_chatbot.messages` qua
`MessageService.create_message`. Message liên kết với conversation bằng `conversation_id`
(bảng `messages` không có cột `session_id`; muốn ra session thì đi qua
`conversation.session_id`).

Bảng không có cột `role`, và luồng hiện tại chỉ ghi tin của user (tin assistant còn là
placeholder TODO), nên mọi row hiện đều là tin người dùng.

### Tóm tắt

- **Tin nhắn đầu tiên**: 3 row — `conversation` + `chat_session` + `messages`.
- **Các tin nhắn sau**: 1 row — `messages` (tái dùng `conversation_id`).
- **Tin của assistant**: chưa persist (placeholder TODO).

## Việc còn lại (TODO)

- Thay phản hồi tự động trong `ChatState.append_exchange` bằng logic gọi LLM/backend
  thật, và persist cả tin của assistant vào `ai_chatbot.messages` (hiện chỉ ghi tin user).
  Cần thống nhất convention lưu role vì bảng không có cột `role`.
- Cân nhắc cơ chế "pending + spinner" cho lúc gọi API để UI không đứng im khi chờ
  (xem ghi chú về `on_click` ở trên).

## Kiểm thử

Kiểm tra import:

```bash
.venv/bin/python -c "from components.chat.floating_chat import FloatingChat"
```

Lệnh trên cần dependency đầy đủ (bao gồm Databricks SDK). Nếu thiếu, chạy `uv sync`
trước.
