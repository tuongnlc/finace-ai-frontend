import streamlit as st

from components.news.news_list import (
    NewsList,
    load_summaries,
    render_date_range_filter,
    show_pending_toast,
)


def market_news():
    st.set_page_config(
        page_title="Market News",
        layout="wide"
    )

    show_pending_toast()

    start_date, end_date = render_date_range_filter()

    NewsList(
        load_summaries(start_date, end_date),
        start_date=start_date,
        end_date=end_date,
        key="market_news",
    ).render(show_actions=True)


market_news()
