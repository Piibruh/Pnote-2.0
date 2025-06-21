import streamlit as st
from config import GEMINI_API_KEY
from ui.sidebar import display_sidebar
from core.services import ai_service, course_manager_service

# ==============================================================================
# TRANG WORKSPACE
# Ghi chú: Đây là không gian làm việc chính, nơi người dùng tương tác với AI,
# tài liệu và các công cụ khác. Trang này được thiết kế theo bố cục 3 phần
# (Sidebar, Chat, Ghi chú) để tối ưu hóa năng suất.
# ==============================================================================

# --- Cấu hình Trang và Kiểm tra State ---
st.set_page_config(
    page_title="PNote Workspace",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded" # Luôn mở sidebar trong workspace
)

# --- Load CSS và Khởi tạo State ---
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Khởi tạo state toàn cục một cách an toàn.
# Điều này đảm bảo app không bị lỗi khi người dùng refresh trang workspace.
if "courses" not in st.session_state:
    st.session_state.courses = course_manager_service.list_courses()
if "current_course_id" not in st.session_state:
    st.session_state.current_course_id = None
if "current_course_name" not in st.session_state:
    st.session_state.current_course_name = None

# --- Logic kiểm tra và điều hướng ---
# Đảm bảo người dùng không thể vào trang này trực tiếp mà không chọn khóa học.
if not st.session_state.current_course_id:
    st.warning("Vui lòng chọn một khóa học từ Dashboard để bắt đầu.")
    if st.button("Trở về Dashboard", use_container_width=True):
        st.switch_page("app.py")
    st.stop() # Dừng thực thi nếu không có khóa học nào được chọn.

# --- Hiển thị Giao Diện Chính ---
display_sidebar()

# --- Bố Cục Nội Dung Chính ---
course_id = st.session_state.current_course_id
course_name = st.session_state.current_course_name

# Khởi tạo các state dành riêng cho workspace này nếu chưa có.
# Dùng key động để mỗi khóa học có một lịch sử chat và ghi chú riêng.
if f"messages_{course_id}" not in st.session_state:
    st.session_state[f"messages_{course_id}"] = [{"role": "assistant", "content": f"Xin chào! Bắt đầu cuộc trò chuyện về **{course_name}**."}]
if f"notes_{course_id}" not in st.session_state:
    st.session_state[f"notes_{course_id}"] = f"# Ghi chú cho {course_name}\n\n"

# Cấu trúc 2 cột chính: Chat và Ghi chú.
chat_col, note_col = st.columns([3, 2])

with chat_col:
    st.header("💬 Thảo Luận Với AI", anchor=False, divider="gray")
    # Khung chứa tin nhắn, đặt chiều cao cố định để có thanh cuộn.
    chat_container = st.container(height=600, border=False)
    with chat_container:
        for message in st.session_state[f"messages_{course_id}"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Khung nhập liệu nằm bên dưới.
    if prompt := st.chat_input("Hỏi PNote điều gì đó..."):
        # Thêm tin nhắn của người dùng vào state và hiển thị ngay lập tức.
        st.session_state[f"messages_{course_id}"].append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
        
        # Xử lý và nhận câu trả lời từ bot.
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("PNote đang suy nghĩ..."):
                    response = ai_service.get_chat_answer(course_id, prompt)
                    st.markdown(response)
        # Lưu câu trả lời của bot vào state.
        st.session_state[f"messages_{course_id}"].append({"role": "assistant", "content": response})

with note_col:
    st.header("🗒️ Ghi Chú Cá Nhân", anchor=False, divider="gray")
    note_content = st.text_area(
        "Ghi chú cá nhân của bạn...",
        value=st.session_state[f"notes_{course_id}"],
        height=650, 
        label_visibility="collapsed"
    )
    # Tự động lưu ghi chú khi có thay đổi.
    if note_content != st.session_state[f"notes_{course_id}"]:
        st.session_state[f"notes_{course_id}"].append(note_content)
        st.toast("Đã lưu ghi chú!", icon="✅")
