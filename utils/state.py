# Ghi chú: Quản lý trạng thái của ứng dụng một cách tập trung.
import streamlit as st
from core.services import course_manager_service

def initialize_session_state():
    """Khởi tạo tất cả các biến cần thiết trong st.session_state."""
    if "courses" not in st.session_state:
        st.session_state.courses = course_manager_service.list_courses()
    
    if "current_course" not in st.session_state:
        st.session_state.current_course = st.session_state.courses[0] if st.session_state.courses else None

    if "messages" not in st.session_state:
        st.session_state.messages = {}
        
    if "notes" not in st.session_state:
        st.session_state.notes = {} 