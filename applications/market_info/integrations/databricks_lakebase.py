"""Tiện ích dùng chung cho Databricks Lakebase Data API (PostgREST).

Gom cấu hình, xác thực OAuth M2M và HTTP session về một chỗ để mọi client
dùng chung MỘT ``WorkspaceClient`` và MỘT connection pool. Nhờ đó token chỉ
được lấy một lần và TLS handshake chỉ mở một lần, giúp lần gửi tin đầu tiên
nhanh hơn đáng kể (đặc biệt trên mạng di động).
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time

import requests
from databricks.sdk import WorkspaceClient

from config import get_secret


# Base URL mặc định của Lakebase Data API (có thể override qua biến môi trường
# hoặc secrets.toml với key DATABRICKS_LAKEBASE_API_BASE).
_DEFAULT_LAKEBASE_API_BASE = (
    "https://ep-ancient-pine-d8w8ldyd.database.us-east-2.cloud.databricks.com"
    "/api/2.0/workspace/7474647713604067/rest/databricks_postgres"
)

# Token OAuth M2M của Databricks sống khoảng 1 giờ. Cache lại và chỉ làm mới
# sớm trước khi hết hạn một khoảng, tránh dùng phải token vừa hết hạn.
_TOKEN_REFRESH_MARGIN_SECONDS = 300
# Fallback nếu không đọc được hạn (exp) từ token.
_TOKEN_FALLBACK_TTL_SECONDS = 55 * 60

_workspace_client: WorkspaceClient | None = None
_http_session: requests.Session | None = None
_auth_headers: dict[str, str] | None = None
_auth_expires_at: float = 0.0
_auth_lock = threading.Lock()
_warm_lock = threading.Lock()
_warmed_up = False


def _setting(name: str) -> str | None:
    """Đọc cấu hình Databricks: ưu tiên biến môi trường, fallback secrets.toml."""
    return os.environ.get(name) or get_secret(name)


def _require(name: str, default: str | None = None) -> str:
    value = _setting(name) or default
    if not value:
        raise RuntimeError(
            f"Thiếu cấu hình '{name}'. Khai báo trong biến môi trường "
            f"hoặc .streamlit/secrets.toml."
        )
    return value


def get_workspace_client() -> WorkspaceClient:
    """WorkspaceClient dùng chung để lấy token OAuth M2M."""
    global _workspace_client
    if _workspace_client is None:
        _workspace_client = WorkspaceClient(
            host=_require("DATABRICKS_HOST"),
            client_id=_require("DATABRICKS_CLIENT_ID"),
            client_secret=_require("DATABRICKS_CLIENT_SECRET"),
            auth_type="oauth-m2m",
        )
    return _workspace_client


def _token_expiry(headers: dict[str, str]) -> float | None:
    """Đọc hạn (``exp``) từ JWT trong header ``Authorization``.

    Trả về epoch giây, hoặc ``None`` nếu token không phải JWT/không có ``exp``.
    """
    authorization = headers.get("Authorization", "")
    _, _, token = authorization.partition(" ")
    parts = token.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        claims = json.loads(base64.urlsafe_b64decode(payload + padding))
    except Exception:
        return None
    exp = claims.get("exp")
    return float(exp) if exp else None


def databricks_auth() -> dict[str, str]:
    """Header Authorization (OAuth M2M), cache lại tới gần lúc token hết hạn.

    Token OAuth M2M của Databricks có hạn khoảng 1 giờ, nên cache lại để không
    phải xin token mới cho mỗi request; tự làm mới sớm trước khi hết hạn.
    """
    global _auth_headers, _auth_expires_at
    now = time.time()
    if _auth_headers is not None and now < _auth_expires_at:
        return _auth_headers

    with _auth_lock:
        now = time.time()
        if _auth_headers is not None and now < _auth_expires_at:
            return _auth_headers

        headers = get_workspace_client().config.authenticate()
        expiry = _token_expiry(headers)
        if expiry is None:
            _auth_expires_at = now + _TOKEN_FALLBACK_TTL_SECONDS
        else:
            _auth_expires_at = expiry - _TOKEN_REFRESH_MARGIN_SECONDS
        _auth_headers = headers
        return headers


def get_http_session() -> requests.Session:
    """Dùng chung 1 HTTP session để tái sử dụng connection pool."""
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
    return _http_session


def lakebase_api_base() -> str:
    """Base URL của Lakebase Data API."""
    return _require(
        "DATABRICKS_LAKEBASE_API_BASE", default=_DEFAULT_LAKEBASE_API_BASE
    )


def warm_up() -> None:
    """Chủ động lấy token + mở sẵn kết nối tới Lakebase ở luồng nền.

    Phải gọi trong luồng Streamlit (nơi đọc được ``st.secrets``) để cấu hình
    được nạp trước; phần gọi mạng chạy nền nên không chặn UI. Nhờ vậy lần gửi
    tin đầu tiên không phải chờ OAuth token và TLS handshake. Là best-effort:
    mọi lỗi đều bị bỏ qua vì lỗi thật sẽ hiện ra khi gửi tin.
    """
    global _warmed_up
    with _warm_lock:
        if _warmed_up:
            return
        _warmed_up = True

    # Khởi tạo client/session ngay tại luồng chính để đọc được secrets.
    try:
        get_workspace_client()
        get_http_session()
        base = lakebase_api_base()
    except Exception:
        return

    def _warm() -> None:
        try:
            databricks_auth()
            # Chỉ cần mở sẵn TCP + TLS tới host Lakebase; 401 là bình thường.
            get_http_session().get(base, timeout=10)
        except Exception:
            pass

    threading.Thread(target=_warm, daemon=True).start()
