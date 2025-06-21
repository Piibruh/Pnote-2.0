# Ghi chú: File này vẽ sidebar chứa các công cụ AI và quản lý tài liệu cho Workspace.
# Phiên bản này được nâng cấp để lưu trữ file gốc trước khi xử lý.

import streamlit as st
import time
import os # Thư viện để tương tác với hệ điều hành (tạo thư mục, đường dẫn)
from core.services import course_manager_service, document_processor_service, ai_service, slugify

def display_sidebar():
    """
    Vẽ toàn bộ nội dung của sidebar và xử lý logic của nó.
    Bao gồm các chức năng: Thêm tài liệu, Công cụ AI, và các tùy chọn khác.
    """
    with st.sidebar:
        # --- Logo và Tiêu đề ---
        st.markdown(
            """
            <div class="logo-box">
                <span class="logo-text">P</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.title(f"PNote Workspace")
        st.caption(f"Khóa học: **{st.session_state.get('current_course_name', '')}**")
        st.markdown("---")

        # --- Chức năng Thêm tài liệu ---
        with st.expander("➕ Thêm tài liệu vào khóa học", expanded=True):
            # Cho phép tải lên nhiều file cùng lúc
            uploaded_files = st.file_uploader(
                "1. Tải file (PDF, DOCX)",
                type=["pdf", "docx"],
                accept_multiple_files=True
            )
            url_input = st.text_input(
                "2. Nhập URL (bài báo, YouTube)",
                placeholder="https://..."
            )
            pasted_text = st.text_area(
                "3. Dán văn bản vào đây",
                placeholder="Dán nội dung từ clipboard..."
            )
            
            if st.button("Xử lý và Thêm", use_container_width=True):
                with st.spinner("⏳ Đang xử lý tài liệu..."):
                    processed_count = 0
                    course_id = st.session_state.current_course_id
                    
                    # --- BỔ SUNG: Logic lưu trữ file vật lý ---
                    # Tạo thư mục riêng cho từng khóa học để quản lý file dễ dàng
                    course_data_path = os.path.join("data", course_id)
                    os.makedirs(course_data_path, exist_ok=True)
                    
                    # 1. Xử lý các file được tải lên
                    if uploaded_files:
                        for uploaded_file in uploaded_files:
                            # Tạo một đường dẫn an toàn để lưu file
                            file_path = os.path.join(course_data_path, uploaded_file.name)
                            
                            # Ghi file từ bộ nhớ ra đĩa
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getvalue())
                            
                            # Bây giờ, thay vì xử lý file trong bộ nhớ, chúng ta sẽ mở lại
                            # file vừa lưu để xử lý. Điều này đảm bảo tính nhất quán.
                            with open(file_path, "rb") as f_to_process:
                                file_type = uploaded_file.name.split('.')[-1]
                                text, source_name = document_processor_service.extract_text(file_type, f_to_process)
                                if text:
                                    course_manager_service.add_document(course_id, text, source_name)
                                    processed_count += 1
                    
                    # 2. Xử lý URL (không cần lưu file)
                    if url_input:
                        text, source_name = document_processor_service.extract_text('url', url_input)
                        if text:
                            course_manager_service.add_document(course_id, text, source_name)
                            processed_count += 1
                    
                    # 3. Xử lý văn bản dán vào (không cần lưu file)
                    if pasted_text:
                        text, source_name = document_processor_service.extract_text('text', pasted_text)
                        if text:
                            course_manager_service.add_document(course_id, text, source_name)
                            processed_count += 1
                    
                    # Thông báo kết quả
                    if processed_count > 0:
                        st.success(f"Hoàn tất! Đã xử lý {processed_count} nguồn tài liệu.")
                        st.info("Hệ thống đã sẵn sàng để chat.")
                        time.sleep(1) # Chờ một chút để người dùng đọc thông báo
                    else:
                        st.warning("Không có tài liệu nào hợp lệ để xử lý.")

        # --- Công cụ AI ---
        st.markdown("---")
        st.header("🛠️ AI Toolkit", anchor=False)
        
        # Các công cụ AI (Tóm tắt, Quiz, Từ khóa) giữ nguyên logic
        with st.expander("📄 Tóm tắt Khóa học"):
            # ... (Giữ nguyên code)
            pass
        with st.expander("❓ Tạo Câu Hỏi Ôn Tập"):
            # ... (Giữ nguyên code)
            pass
        with st.expander("🔑 Trích Xuất Từ Khóa"):
            # ... (Giữ nguyên code)
            pass

        # --- Tùy chọn Nâng cao và Điều hướng ---
        st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
        with st.expander("⚠️ Tùy chọn Nâng cao"):
            st.warning("Hành động này không thể hoàn tác!")
            if st.button("Xóa Khóa Học Này", use_container_width=True, type="primary"):
                # ... (Giữ nguyên code)
                pass

        st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
        if st.button("⬅️ Trở về Dashboard", use_container_width=True):
            st.switch_page("app.py")
