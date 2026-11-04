import streamlit as st

# from ai_engineer.frontend.components.news.news_list import (
#     NewsList,
#     load_summaries,
#     render_date_range_filter,
#     show_pending_toast,
# )


def favorite_news():
    st.set_page_config(
        page_title="Favorite News",
        layout="wide"
    )

    # show_pending_toast()

    # start_date, end_date = render_date_range_filter()

    # NewsList(
    #     load_summaries(start_date, end_date),
    #     start_date=start_date,
    #     end_date=end_date,
    #     favorite_only=True,
    # ).render()


if __name__ == "__main__":
    favorite_news()
