import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from applications.market_info.integrations.databricks_lakebase import warm_up
from components.chat.floating_chat import FloatingChat

# Khởi động sớm ngay khi page bắt đầu render: lấy token OAuth + mở sẵn kết nối
# tới Lakebase ở luồng nền, để lần gửi tin đầu tiên không phải chờ token/TLS.
warm_up()

# MARKET INFO PAGE
market_news_page = st.Page(
    "pages/market_info/market_news.py",
    title="Tin tức thị trường",
    icon="📰",
)


pg = st.navigation({
    "THÔNG TIN KINH TẾ": [
        market_news_page,
    ],
    
}, position="sidebar")

pg.run()

# Nút chat nổi dùng chung cho mọi page.
# Render sau pg.run() để không phá vỡ set_page_config() phải là lệnh đầu tiên của page.
FloatingChat().render()
