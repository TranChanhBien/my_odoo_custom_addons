/** @odoo-module **/

document.addEventListener("click", function (e) {
    const img = e.target;

    // Chỉ áp dụng cho ảnh trong list hoặc form
    if (img.tagName === "IMG" && img.closest(".o_list_view, .o_form_view")) {

        // Tránh click vào icon nhỏ (optional)
        if (!img.src || img.src.startsWith("data:image") || img.src.startsWith("http")) {

            const modal = document.createElement("div");
            modal.className = "img-preview-modal";

            const previewImg = document.createElement("img");
            previewImg.src = img.src;

            modal.appendChild(previewImg);

            // Click nền để đóng
            modal.addEventListener("click", () => modal.remove());

            // ESC để đóng
            document.addEventListener("keydown", function escHandler(ev) {
                if (ev.key === "Escape") {
                    modal.remove();
                    document.removeEventListener("keydown", escHandler);
                }
            });

            document.body.appendChild(modal);
        }
    }
});