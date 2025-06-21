import streamlit as st
from core.services import course_manager_service, slugify
import time

st.set_page_config(
    page_title="PNote Dashboard",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed" # Ẩn sidebar trên trang này
)

# --- Load CSS ---
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Khởi tạo State ---
if "courses" not in st.session_state:
    st.session_state.courses = course_manager_service.list_courses()

# --- Giao diện Dashboard ---
st.title("My Workspace")
st.text("Chào mừng trở lại! Chọn một khóa học để bắt đầu hoặc tạo một khóa học mới.")
st.markdown("---")

# --- Phần tạo khóa học mới ---
with st.expander("➕ Tạo khóa học mới", expanded=True):
    with st.form("new_course_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_course_name_input = st.text_input("Tên khóa học", placeholder="vd: Lịch sử Đảng Cộng sản Việt Nam")
        with col2:
            submitted = st.form_submit_button("Tạo Ngay", use_container_width=True)
        
        if submitted:
            if not new_course_name_input:
                st.warning("Vui lòng nhập tên khóa học.")
            else:
                safe_name = slugify(new_course_name_input)
                if len(safe_name) < 3:
                    st.error("Lỗi: Tên khóa học phải có ít nhất 3 ký tự (chữ hoặc số).")
                elif any(course['id'] == safe_name for course in st.session_state.courses):
                    st.warning(f"Khóa học '{new_course_name_input}' đã tồn tại.")
                else:
                    with st.spinner(f"Đang tạo khóa học '{new_course_name_input}'..."):
                        # Lưu cả tên gốc vào metadata
                        course_manager_service.get_or_create_course_collection(safe_name, new_course_name_input)
                        st.session_state.courses.append({"id": safe_name, "name": new_course_name_input})
                        st.success(f"Đã tạo '{new_course_name_input}'!")
                        time.sleep(1); st.rerun()

st.markdown("---")

# --- Hiển thị các khóa học dưới dạng card ---
if not st.session_state.courses:
    st.info("Bạn chưa có khóa học nào. Hãy tạo một khóa học mới ở trên để bắt đầu!")
else:
    cols = st.columns(4)
    for i, course in enumerate(st.session_state.courses):
        col = cols[i % 4]
        with col:
            # Dùng st.markdown để inject class CSS cho card
            st.markdown(
                f"""
                <div class="course-card">
                    <h3>{course['name']}</h3>
                    <p>ID: {course['id']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Mở Workspace", key=f"enter_{course['id']}", use_container_width=True):
                st.session_state.current_course_id = course['id']
                st.session_state.current_course_name = course['name']
                st.switch_page("pages/workspace.py")