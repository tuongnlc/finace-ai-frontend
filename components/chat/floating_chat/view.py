VIEWPORT_SCRIPT = """
<script>
(() => {
    // Yêu cầu trình duyệt co lại layout viewport khi bàn phím ảo mở ra
    // (Android Chrome). Nếu không, bàn phím sẽ đè lên các phần tử position:fixed.
    const meta = document.querySelector('meta[name="viewport"]');
    if (meta) {
        const content = meta.getAttribute("content") || "";
        if (!content.includes("interactive-widget")) {
            meta.setAttribute("content", content + ", interactive-widget=resizes-content");
        }
    }

    let rafId = null;
    const updateViewport = () => {
        if (rafId) cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(() => {
            const vv = window.visualViewport;
            const height = vv?.height || window.innerHeight;
            const top = vv?.offsetTop || 0;
            document.documentElement.style.setProperty(
                "--floating-chat-viewport-height",
                `${height}px`
            );
            document.documentElement.style.setProperty(
                "--floating-chat-viewport-top",
                `${top}px`
            );
        });
    };

    updateViewport();
    if (!window.__floatingChatInited) {
        window.__floatingChatInited = true;
        window.visualViewport?.addEventListener("resize", updateViewport);
        window.visualViewport?.addEventListener("scroll", updateViewport);
        window.addEventListener("resize", updateViewport);
        window.addEventListener("orientationchange", updateViewport);
        // Khi ô nhập được focus (bàn phím mở), cập nhật lại chiều cao khung chat
        // vì một số trình duyệt cập nhật visualViewport trễ một chút.
        document.addEventListener("focusin", (e) => {
            if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) {
                setTimeout(updateViewport, 100);
                setTimeout(updateViewport, 350);
            }
        });
    }
})();
</script>
"""

