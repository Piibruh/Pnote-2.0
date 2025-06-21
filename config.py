# Ghi chú: File này chứa tất cả các hằng số và cấu hình của ứng dụng.
import os
# Thêm 2 dòng này để đọc file .env
from dotenv import load_dotenv
load_dotenv()

# --- Cấu hình API và Model ---
# ĐÃ SỬA: Đọc API Key từ file .env một cách an toàn.
# os.getenv sẽ tìm biến môi trường có tên 'GEMINI_API_KEY'.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GENERATIVE_MODEL_NAME = 'gemini-pro'
EMBEDDING_MODEL_NAME = 'models/embedding-001'

# --- Cấu hình xử lý văn bản (RAG) ---
TEXT_CHUNK_SIZE = 800
TEXT_CHUNK_OVERLAP = 100
VECTOR_DB_SEARCH_RESULTS = 5

# --- Cấu hình ứng dụng ---
CHROMA_DB_PATH = "./pnote_chroma_db"