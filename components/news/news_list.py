from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

import polars as pl
import streamlit as st

from applications.market_info.services.newspaper_summary.newspaper_summary_service import (
    NewspaperSummaryService,
)
from components.filter.date_filter import DateFilter
from components.filter.multi_select_dropdown_filter import (
    MultiSelectDropdownFilter,
)
from components.markdown.markdown import MarkDown

DEFAULT_TITLE = "TIN TỨC THỊ TRƯỜNG"
FAVORITE_TOAST_KEY = "favorite_toast"

NEWS_SCHEMA = {
    "summary_id": pl.Utf8,
    "publish_date": pl.Date,
    "news_type": pl.Utf8,
    "news_summary": pl.Utf8,
    "sentiment_analysis": pl.Utf8,
    "main_topic": pl.Utf8,
    "stocks_mention": pl.Utf8,
    "fund_name": pl.Utf8,
    "circular_and_policy": pl.Utf8,
    "legal_documents_and_regulations": pl.Utf8,
}

# Options của filter sau dựa trên kết quả của filter trước
CASCADING_FILTERS = [
    ("Công ty liên quan", "stocks_mention"),
    ("Trạng thái", "sentiment_analysis"),
    ("Chủ đề", "main_topic"),
]


@st.cache_data(ttl=300, show_spinner=False)
def load_summaries(start_date: date, end_date: date):
    """Cache danh sách tin tức để không phải gọi lại backend mỗi lần rerun."""
    return NewspaperSummaryService().list_summaries(start_date, end_date)


def clear_summaries_cache() -> None:
    """Xóa cache sau khi thêm/xóa tin để lần render sau lấy dữ liệu mới."""
    load_summaries.clear()


def show_pending_toast() -> None:
    """Hiển thị popup sau khi rerun."""
    toast_message = st.session_state.pop(FAVORITE_TOAST_KEY, None)
    if toast_message:
        st.toast(toast_message, icon="✅")


def render_date_range_filter(days: int = 90) -> tuple[date, date]:
    max_date = date.today()
    min_date = max_date - timedelta(days=days)
    filter_col, _ = st.columns([2, 1])
    with filter_col:
        return DateFilter(min_date=min_date, max_date=max_date).render()


def _unique_options(df: pl.DataFrame, column: str) -> list:
    """Lấy danh sách giá trị duy nhất của một cột."""
    if df.is_empty() or column not in df.columns:
        return []
    return df[column].unique().drop_nulls().sort().to_list()


def _filter_by_values(df: pl.DataFrame, column: str, selected: list) -> pl.DataFrame:
    """Giữ các dòng có giá trị nằm trong `selected`."""
    if not selected:
        return df.head(0)
    return df.filter(pl.col(column).is_in(selected))


class NewsList:
    """Khối danh sách tin tức dùng chung cho các page (tin thị trường, tin theo dõi)."""

    def __init__(
        self,
        summaries: Iterable,
        start_date: date,
        end_date: date,
        favorite_only: bool = False,
        title: str = DEFAULT_TITLE,
    ):
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        if favorite_only:
            summaries = [item for item in summaries if item.is_favorite == 1]
        else:
            summaries = [item for item in summaries if item.is_favorite == 0]
        self.news = self._to_dataframe(summaries)

    def render(self, show_actions: bool = False) -> None:
        news = self._apply_cascading_filters()

        st.divider()
        MarkDown(font_size="28px", text=self.title).render()
        st.write(
            f"Xem tin tức thị trường đáng chú ý ngày: {self.start_date} đến {self.end_date}"
        )

        for idx, item in enumerate(news.to_dicts()):
            self._render_card(item, idx, show_actions)

    @staticmethod
    def _to_dataframe(summaries: Iterable) -> pl.DataFrame:
        return pl.DataFrame(
            [
                {
                    "summary_id": str(item.summary_id),
                    "publish_date": item.publish_date,
                    "news_type": item.newspaper_type,
                    "news_summary": item.newspaper_summary,
                    "sentiment_analysis": item.sentiment_analysis,
                    "main_topic": item.main_topic,
                    "stocks_mention": item.stocks_mention,
                    "fund_name": item.fund_name,
                    "circular_and_policy": item.circular_and_policy,
                    "legal_documents_and_regulations": item.legal_documents_and_regulations,
                }
                for item in summaries
            ],
            schema=NEWS_SCHEMA,
        ).sort("publish_date", descending=True)

    def _apply_cascading_filters(self) -> pl.DataFrame:
        news = self.news
        filter_cols = st.columns(len(CASCADING_FILTERS))
        for (filter_name, column), filter_col in zip(CASCADING_FILTERS, filter_cols):
            with filter_col:
                selected_values = MultiSelectDropdownFilter(
                    filter_name=filter_name,
                    options=_unique_options(news, column),
                ).render()
            news = _filter_by_values(news, column, selected_values)
        return news

    @staticmethod
    def _render_card(item: dict, idx: int, show_actions: bool) -> None:
        with st.container(border=True):
            st.caption(
                f":blue[Ngày đăng: {item.get('publish_date')} - "
                f"Trạng thái: {item.get('sentiment_analysis')}]"
            )
            st.caption(f":blue[Loại tin tức: {item.get('news_type')}]")

            st.write(item.get("news_summary"))

            if item.get("stocks_mention"):
                st.caption(f":green[Chứng khoán liên quan: {item.get('stocks_mention')}]")
            if item.get("fund_name"):
                st.caption(f":green[Quỹ liên quan: {item.get('fund_name')}]")

            if item.get("circular_and_policy"):
                st.caption(
                    f":red[Thông tư và chính sách liên quan: {item.get('circular_and_policy')}]"
                )
            if item.get("legal_documents_and_regulations"):
                st.caption(
                    f":red[Văn bản pháp luật liên quan: "
                    f"{item.get('legal_documents_and_regulations')}]"
                )

            if show_actions:
                _render_card_actions(item, idx)


def _render_card_actions(item: dict, idx: int) -> None:
    summary_id = item.get("summary_id")
    delete_col, follow_col, _ = st.columns([1, 3, 2], gap="small")
    with delete_col:
        if st.button("Xóa", key=f"delete_{idx}"):
            NewspaperSummaryService().delete_summaries(summary_id)
            clear_summaries_cache()
            st.rerun()
    with follow_col:
        if st.button("Thêm vào danh sách theo dõi", key=f"follow_{idx}"):
            NewspaperSummaryService().add_to_favorite(summary_id)
            st.session_state[FAVORITE_TOAST_KEY] = "Thêm vào danh sách theo dõi thành công!"
            clear_summaries_cache()
            st.rerun()
