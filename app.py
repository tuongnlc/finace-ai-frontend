import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# MARKET INFO PAGE
market_news_page = st.Page(
    "pages/market_info/market_news.py",
    title="Tin tức thị trường",
    icon="📰",
)

favorite_news_page = st.Page(
    "pages/market_info/favorite_news.py",
    title="Tin tức đáng chú ý",
    icon="📰",
)

pg = st.navigation({
    "THÔNG TIN KINH TẾ": [
        market_news_page,
        favorite_news_page,
    ],
    
}, position="sidebar")