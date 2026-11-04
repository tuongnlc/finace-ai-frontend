import streamlit as st


class MultiSelectDropdownFilter:
    def __init__(self, filter_name: str, options: list[dict], default: list[dict] = None):
        self.filter_name = filter_name
        self.options = options
        self.default = default
        
        # Định nghĩa 1 item đại diện cho "Select All"
        self.ALL_OPTION = {"label": "Select All", "value": "ALL"}

    def render(self):
        # 1. Chèn lựa chọn "Select All" vào đầu danh sách options
        augmented_options = [self.ALL_OPTION] + self.options

        # 2. Định nghĩa giá trị mặc định ban đầu là "Select All" (chỉ hiện đúng 1 thẻ)
        default_selected = [self.ALL_OPTION] if self.default is None else self.default

        # 3. Hiển thị multiselect
        selected = st.multiselect(
            label=self.filter_name,
            options=augmented_options,
            default=default_selected,
            # Giúp Streamlit hiển thị đúng chữ 'label' nếu option là dict
            format_func=lambda x: x.get("label", str(x)) if isinstance(x, dict) else str(x)
        )

        # 4. Logic ngầm: Nếu trong danh sách chọn có "Select All" -> Trả về toàn bộ options thực tế
        if self.ALL_OPTION in selected:
            return self.options
        
        return selected