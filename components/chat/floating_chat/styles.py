# Popover trong Streamlit render dạng: stPopover > div > (wrapper) > button[stPopoverButton].
# Nên phải style theo data-testid="stPopoverButton", không dùng selector `> button`.
STYLES = """
<style>
/* Ghim nút chat vào góc phải dưới màn hình.
   Lưu ý: container stPopover mặc định có width:100%, nếu không reset width/left
   thì khối sẽ trải hết chiều ngang và nút bị đẩy về tận mép trái. */
div[data-testid="stPopover"] {
    position: fixed;
    bottom: 24px;
    right: 24px;
    left: auto !important;
    width: auto !important;
    z-index: 9999;
}

/* Nút tròn nổi bật */
div[data-testid="stPopover"] [data-testid="stPopoverButton"] {
    width: 60px !important;
    height: 60px !important;
    min-height: 60px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    background-color: #FF4B4B !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    font-size: 24px !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s ease;
}

div[data-testid="stPopover"] [data-testid="stPopoverButton"]:hover {
    transform: scale(1.08);
    background-color: #ff3333 !important;
    color: #FFFFFF !important;
}

/* Ẩn mũi tên mặc định của popover */
div[data-testid="stPopover"] [data-testid="stPopoverButton"] svg {
    display: none !important;
}

/* Khung chat bung ra (desktop) */
div[data-testid="stPopoverBody"] {
    width: min(380px, calc(100vw - 32px)) !important;
    max-width: calc(100vw - 32px) !important;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

/* Mobile: chuyển popover thành khung chat toàn màn hình. */
@media (max-width: 640px) {
    div[data-testid="stPopoverBody"] {
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: var(--floating-chat-viewport-height, 100dvh) !important;
        max-height: none !important;
        max-width: none !important;
        min-width: 0 !important;
        transform: none !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
        border-radius: 0 !important;
        padding:
            calc(12px + env(safe-area-inset-top, 0px))
            12px
            calc(12px + env(safe-area-inset-bottom, 0px)) !important;
        z-index: 2147483000 !important;
    }

    /* Cấu trúc DOM thật của Streamlit popover:
       stPopoverBody
         > [data-testid="stVerticalBlock"]            (container chính, cần là flex)
           > stElementContainer (title)
           > [data-testid="stLayoutWrapper"]           ← flex item, cần flex:1
             > .st-key-floating_chat_history          (class key nằm ở đây)
           > form

       Lưu ý: class "st-key-..." nằm trên stVerticalBlock BÊN TRONG stLayoutWrapper,
       không phải trên stLayoutWrapper. Nên phải dùng :has() để target đúng wrapper. */

    /* Container chính (con trực tiếp của popover body) là flex column. */
    div[data-testid="stPopoverBody"] > [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
        width: 100% !important;
        height: 100% !important;
        min-height: 0 !important;
        overflow: hidden !important;
    }

    /* Wrapper của khối lịch sử chat (st.container) - đây mới là flex item
       cần chiếm phần không gian còn trống. height:0 + flex:1 1 0 để bỏ qua
       inline style height:320px và co giãn theo không gian còn lại. */
    div[data-testid="stPopoverBody"] [data-testid="stLayoutWrapper"]:has(.FLOATING_CHAT_HISTORY_KEY) {
        flex: 1 1 0 !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: none !important;
        overflow: hidden !important;
    }

    /* Khối stVerticalBlock bên trong lấp đầy chiều cao của wrapper. */
    div[data-testid="stPopoverBody"] .FLOATING_CHAT_HISTORY_KEY {
        height: 100% !important;
        min-height: 0 !important;
        max-height: none !important;
        overflow-y: auto !important;
        overscroll-behavior: contain;
    }

    /* Form (ô nhập + nút Gửi) cố định ở dưới, không co lại. */
    div[data-testid="stPopoverBody"] form {
        flex: 0 0 auto !important;
        margin-top: 8px !important;
    }

    /* Ô nhập liệu phải >= 16px, nếu không iOS Safari sẽ tự zoom trang
       (làm khung chat phình to và che mất nội dung phía trên). */
    div[data-testid="stPopoverBody"] input,
    div[data-testid="stPopoverBody"] textarea {
        font-size: 16px !important;
    }
}
</style>
"""