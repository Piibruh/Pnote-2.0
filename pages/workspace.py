import streamlit as st
from config import GEMINI_API_KEY
from ui.sidebar import display_sidebar
from core.services import ai_service # Đổi tên cho nhất quán

# --- Cấu hình Trang và Kiểm tra State ---
st.set_page_config(page_title="PNote Workspace", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# Load CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Khởi tạo State ---
# Logic này đảm bảo app không bị lỗi khi người dùng refresh trang workspace
if "courses" not in st.session_state:
    st.session_state.courses = [] # Khởi tạo rỗng, sẽ được đồng bộ khi về dashboard
if "current_course_id" not in st.session_state:
    st.session_state.current_course_id = None
if "current_course_name" not in st.session_state:
    st.session_state.current_course_name = None

# Kiểm tra xem người dùng đã chọn khóa học từ Dashboard chưa
if not st.session_state.current_course_id:
    st.warning("Vui lòng chọn một khóa học từ Dashboard để bắt đầu.")
    if st.button("Trở về Dashboard"):
        st.switch_page("app.py")
    st.stop()

# --- Hiển thị Giao Diện Chính ---
display_sidebar()

# --- Bố Cục Nội Dung Chính ---
course_id = st.session_state.current_course_id
course_name = st.session_state.current_course_name

if f"messages_{course_id}" not in st.session_state:
    st.session_state[f"messages_{course_id}"] = [{"role": "assistant", "content": f"Xin chào! Bắt đầu cuộc trò chuyện về **{course_name}**."}]
if f"notes_{course_id}" not in st.session_state:
    st.session_state[f"notes_{course_id}"] = f"# Ghi chú cho {course_name}\n\n"

chat_col, note_col = st.columns([3, 2])

with chat_col:
    st.header("💬 Thảo Luận Với AI", anchor=False, divider="gray")
    chat_container = st.container(height=600, border=False)
    with chat_container:
        for message in st.session_state[f"messages_{course_id}"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    if prompt := st.chat_input("Hỏi PNote điều gì đó..."):
        st.session_state[f"messages_{course_id}"].append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
        
        with chat_container:
                with st.chat_message("assistant"):
                with st.spinner("PNote đang suy nghĩ..."):
                    response = ai_service.get_chat_answer(course_id, prompt)
                    st.markdown(response)
        st.session_state[f"messages_{course_id}"].append({"role": "assistant", "content": response})

with note_col:
    st.header("🗒️ Ghi Chú Cá Nhân", anchor=False, divider="gray")
    note_content = st.text_area(
        "Ghi chú cá nhân của bạn...",
        value=st.session_state[f"notes_{course_id}"],
        height=650, label_visibility="collapsed"
    )
    if note_content != st.session_state[f"notes_{course_id}"]:
        st.session_state[f"notes_{course_id}"] = note_content
        st.toast("Đã lưu ghi chú!", icon="✅")