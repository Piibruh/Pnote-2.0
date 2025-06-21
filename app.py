import streamlit as st
from core.services import course_manager_service, slugify
import time

# ==============================================================================
# TRANG CHÍNH (DASHBOARD)
# Ghi chú: Đây là trang đầu tiên người dùng nhìn thấy. Nó có nhiệm vụ:
# 1. Hiển thị tất cả các khóa học đã tạo.
# 2. Cho phép tạo một khóa học mới.
# 3. Điều hướng người dùng đến trang Workspace khi họ chọn một khóa học.
# ==============================================================================

# --- Cấu hình Trang Chính ---
# Thiết lập các thông tin cơ bản cho trang Dashboard.
st.set_page_config(
    page_title="PNote Dashboard",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed" # Ẩn sidebar trên trang này vì không cần thiết.
)

# --- Load CSS và Khởi tạo State ---
# Inject file CSS để tùy chỉnh giao diện toàn bộ ứng dụng.
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Khởi tạo session state để lưu trữ dữ liệu giữa các lần tương tác.
# Logic này đảm bảo state chỉ được khởi tạo một lần duy nhất.
if "courses" not in st.session_state:
    st.session_state.courses = course_manager_service.list_courses()

# --- Giao diện Dashboard ---
# Phần logo và tiêu đề chính, tạo ấn tượng ban đầu.
st.markdown(
    """
    <div class="logo-box-large">
        <span class="logo-text-large">P</span>
    </div>
    """,
    unsafe_allow_html=True
)
st.title("PNote Workspace")
st.text("Chào mừng trở lại! Chọn một khóa học để bắt đầu hoặc tạo một không gian làm việc mới.")
st.markdown("---")

# --- Form Tạo Khóa Học Mới ---
# Sử dụng expander để có thể thu gọn, tiết kiệm không gian và làm giao diện sạch hơn.
with st.expander("➕ Tạo khóa học mới", expanded=True):
    with st.form("new_course_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_course_name_input = st.text_input("Tên khóa học (hỗ trợ Tiếng Việt)", placeholder="vd: Lịch sử Đảng Cộng sản Việt Nam")
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
                        # Lưu cả tên gốc vào metadata để hiển thị đẹp hơn.
                        course_manager_service.get_or_create_course_collection(safe_name, new_course_name_input)
                        st.session_state.courses.append({"id": safe_name, "name": new_course_name_input})
                        st.success(f"Đã tạo '{new_course_name_input}'!")
                        
                        # Tự động chuyển trang sau khi tạo thành công.
                        st.session_state.current_course_id = safe_name
                        st.session_state.current_course_name = new_course_name_input
                        time.sleep(1)
                        st.switch_page("pages/workspace.py")

st.markdown("---")
st.header("Danh sách khóa học của bạn", anchor=False)

# --- Hiển thị các khóa học dưới dạng card ---
if not st.session_state.courses:
    st.info("Bạn chưa có khóa học nào. Hãy tạo một khóa học mới ở trên để bắt đầu!")
else:
    # Tạo layout dạng lưới, tối đa 4 cột để tối ưu không gian.
    cols = st.columns(4)
    for i, course in enumerate(st.session_state.courses):
        col = cols[i % 4]
        with col:
            # Dùng st.markdown để inject class CSS cho card, cho phép tùy chỉnh giao diện sâu hơn.
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
