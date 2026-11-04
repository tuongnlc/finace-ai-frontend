import streamlit as st


class DateFilter:
    def __init__(self, min_date, max_date):
        self.min_date = min_date
        self.max_date = max_date
    
    def render(self):
        return st.date_input(
            "Chọn khoảng thời gian",
            value=(self.min_date, self.max_date),
            min_value=self.min_date,
            max_value=self.max_date,
        )
