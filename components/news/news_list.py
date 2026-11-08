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
PAGE_SIZE = 10

NEWS_SCHEMA = {
    "newspaper_url": pl.Utf8,
    "publish_date": pl.Date,
    "stocks_mention": pl.List(pl.Utf8),
    "main_topic": pl.List(pl.Utf8),
    "person_mention": pl.List(pl.Utf8),
    "newspaper_summary": pl.Utf8,
    "sentiment_analysis": pl.Utf8,
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


def render_date_range_filter(days: int = 10) -> tuple[date, date]:
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
        title: str = DEFAULT_TITLE,
        key: str = "news_list",
    ):
        self.title = title
        self.key = key
        self.start_date = start_date
        self.end_date = end_date
        self.news = self._to_dataframe(summaries)

    def render(self, show_actions: bool = False) -> None:
        news, filter_signature = self._apply_cascading_filters()

        st.divider()
        MarkDown(font_size="28px", text=self.title).render()
        st.write(
            f"Xem tin tức thị trường đáng chú ý ngày: {self.start_date} đến {self.end_date}"
        )

        visible = self._resolve_visible_count(news.height, filter_signature)
        for idx, item in enumerate(news.head(visible).to_dicts()):
            self._render_card(item, idx, show_actions)

        self._render_show_more(news.height - visible, visible)

    def _resolve_visible_count(self, total: int, filter_signature: tuple) -> int:
        """Số card đang hiển thị; đổi bộ lọc thì quay về trang đầu."""
        visible_key = f"{self.key}__visible"
        signature_key = f"{self.key}__signature"
        if st.session_state.get(signature_key) != filter_signature:
            st.session_state[signature_key] = filter_signature
            st.session_state[visible_key] = PAGE_SIZE
        return min(st.session_state.get(visible_key, PAGE_SIZE), total)

    def _render_show_more(self, remaining: int, visible: int) -> None:
        """Chỉ render khi còn tin chưa hiển thị; bấm để tải thêm một trang."""
        if remaining <= 0:
            return
        if st.button(f"Xem thêm ({remaining} tin còn lại)", key=f"{self.key}__more"):
            st.session_state[f"{self.key}__visible"] = visible + PAGE_SIZE
            st.rerun()

    @staticmethod
    def _to_dataframe(summaries: Iterable) -> pl.DataFrame:
        return pl.DataFrame(
            [
                {
                    "newspaper_url": item.newspaper_url,
                    "publish_date": item.publish_date,
                    "stocks_mention": item.stocks_mention,
                    "main_topic": item.main_topic,
                    "person_mention": item.person_mention,
                    "newspaper_summary": item.newspaper_summary,
                    "sentiment_analysis": item.sentiment_analysis,
                }
                for item in summaries
            ],
            schema=NEWS_SCHEMA,
        ).sort("publish_date", descending=True)

    def _apply_cascading_filters(self) -> tuple[pl.DataFrame, tuple]:
        news = self.news
        filter_cols = st.columns(len(CASCADING_FILTERS))
        selections = []
        for (filter_name, column), filter_col in zip(CASCADING_FILTERS, filter_cols):
            with filter_col:
                selected_values = MultiSelectDropdownFilter(
                    filter_name=filter_name,
                    options=_unique_options(news, column),
                ).render()
            selections.append(tuple(selected_values or []))
            news = _filter_by_values(news, column, selected_values)
        return news, tuple(selections)

    @staticmethod
    def _render_card(item: dict, idx: int, show_actions: bool) -> None:
        with st.container(border=True):
            st.caption(
                f":blue[Ngày đăng: {item.get('publish_date')} - "
                f"Trạng thái: {item.get('sentiment_analysis')}]"
            )

            st.write(item.get("newspaper_summary"))

            if item.get("stocks_mention"):
                st.caption(
                    f":green[Chứng khoán liên quan: "
                    f"{', '.join(item['stocks_mention'])}]"
                )

            if show_actions:
                _render_card_actions(item, idx)


def _render_card_actions(item: dict, idx: int) -> None:
    newspaper_url = item.get("newspaper_url")
    delete_col, _ = st.columns([1, 5], gap="small")
    with delete_col:
        if st.button("Xóa", key=f"delete_{idx}"):
            NewspaperSummaryService().delete_summaries(newspaper_url)
            clear_summaries_cache()
            st.rerun()
