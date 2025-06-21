import streamlit as st
import time
from core.services import course_manager_service, document_processor_service, ai_service, slugify

def display_sidebar():
    """Vẽ sidebar chứa các công cụ AI và quản lý tài liệu cho Workspace."""
    with st.sidebar:
        # --- Logo ---
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

        # --- Thêm tài liệu ---
        with st.expander("➕ Thêm tài liệu vào khóa học"):
            uploaded_files = st.file_uploader("1. Tải file (PDF, DOCX)", type=["pdf", "docx"], accept_multiple_files=True)
            url_input = st.text_input("2. Nhập URL (bài báo, YouTube)", placeholder="https://...")
            pasted_text = st.text_area("3. Dán văn bản vào đây", placeholder="Dán nội dung từ clipboard...")
            
            if st.button("Xử lý và Thêm", use_container_width=True):
                with st.spinner("⏳ Đang xử lý tài liệu..."):
                    processed_count = 0
                    sources = []
                    if uploaded_files: sources.extend([('pdf' if f.name.endswith('.pdf') else 'docx', f) for f in uploaded_files])
                    if url_input: sources.append(('url', url_input))
                    if pasted_text: sources.append(('text', pasted_text))
                    
                    if not sources:
                        st.warning("Không có tài liệu nào được cung cấp để xử lý.")
                    else:
                        for source_type, source_data in sources:
                            text, source_name = document_processor_service.extract_text(source_type, source_data)
                            if text:
                                course_manager_service.add_document(st.session_state.current_course_id, text, source_name)
                                processed_count += 1
                        st.success(f"Hoàn tất! Đã xử lý {processed_count} nguồn tài liệu.")
                        st.info("Hệ thống sẽ mất vài giây để cập nhật. Vui lòng bắt đầu chat.")
                        time.sleep(1)
        
        # --- Công cụ AI ---
        st.markdown("---")
        st.header("🛠️ AI Toolkit", anchor=False)
        
        with st.expander("📄 Tóm tắt Khóa học"):
            if st.button("Tạo Tóm Tắt", use_container_width=True, key="summarize_btn"):
                with st.spinner("AI đang đọc và tóm tắt toàn bộ tài liệu..."):
                    summary = ai_service.summarize_course(st.session_state.current_course_id)
                    st.session_state.summary = summary
            if "summary" in st.session_state and st.session_state.summary:
                st.text_area("Bản tóm tắt:", value=st.session_state.summary, height=200)

        with st.expander("❓ Tạo Câu Hỏi Ôn Tập"):
            num_questions = st.slider("Số lượng câu hỏi:", 3, 10, 5)
            if st.button("Bắt đầu Tạo Quiz", use_container_width=True, key="quiz_btn"):
                 with st.spinner("AI đang soạn câu hỏi cho bạn..."):
                    quiz = ai_service.generate_quiz(st.session_state.current_course_id, num_questions)
                    st.session_state.quiz = quiz
            if "quiz" in st.session_state and isinstance(st.session_state.quiz, list):
                for i, q in enumerate(st.session_state.quiz):
                    st.write(f"**Câu {i+1}:** {q['question']}")
                    st.radio("Chọn đáp án:", options=q['options'], key=f"q_{i}")

        with st.expander("🔑 Trích Xuất Từ Khóa"):
            if st.button("Tìm Từ Khóa Chính", use_container_width=True, key="keyword_btn"):
                with st.spinner("AI đang phân tích các khái niệm..."):
                    keywords = ai_service.extract_keywords(st.session_state.current_course_id)
                    st.session_state.keywords = keywords
            if "keywords" in st.session_state and st.session_state.keywords:
                st.info(", ".join(st.session_state.keywords))

        # --- Tùy chọn Nâng cao ---
        st.markdown("---")
        with st.expander("⚠️ Tùy chọn Nâng cao"):
            st.warning("Hành động này không thể hoàn tác!")
            if st.button("Xóa Khóa Học Này", use_container_width=True, type="primary"):
                course_to_delete_id = st.session_state.current_course_id
                course_to_delete_name = st.session_state.current_course_name
                with st.spinner(f"Đang xóa khóa học '{course_to_delete_name}'..."):
                    success, message = course_manager_service.delete_course(course_to_delete_id)
                    if success:
                        st.session_state.courses = [c for c in st.session_state.courses if c['id'] != course_to_delete_id]
                        st.success(message)
                        time.sleep(1); st.switch_page("app.py")
                    else:
                        st.error(message)

        # --- Nút điều hướng ---
        st.markdown("---")
        if st.button("⬅️ Trở về Dashboard", use_container_width=True):
            st.switch_page("app.py")