import streamlit as st

class MarkDown:
    def __init__(
            self, 
            text: str,
            font_size: str = "24px",
            font_weight: str = "bold",
            color: str = "#1583b4",
        ):
        self.text = text
        self.font_size = font_size
        self.font_weight = font_weight
        self.color = color

    def render(self):
        st.markdown(
            f"""
            <p style='font-size: {self.font_size}; font-weight: {self.font_weight}; color: {self.color};'>{self.text}</p>
            """,
            unsafe_allow_html=True,
        )



