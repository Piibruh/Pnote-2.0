# Ghi chú: "Bộ não" của ứng dụng. File này chứa toàn bộ logic xử lý dữ liệu và AI.
# Nó được thiết kế để hoàn toàn độc lập với giao diện người dùng (không import streamlit).
# Phiên bản này được viết lại để dài hơn, rõ ràng hơn và đầy đủ chức năng hơn.

# ==============================================================================
# ĐOẠN CODE BẮT BUỘC ĐỂ SỬA LỖI SQLITE3 TRÊN STREAMLIT CLOUD
# Đoạn code này phải được đặt ở ĐẦU TIÊN, trước tất cả các import khác.
# Nó ép buộc Python sử dụng phiên bản SQLite mới mà chúng ta đã cài.
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# ==============================================================================

import google.generativeai as genai
import chromadb
from pypdf import PdfReader
import docx
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import tiktoken
import time
import re
import json
from unicodedata import normalize
from config import (
    GEMINI_API_KEY, GENERATIVE_MODEL_NAME, TEXT_CHUNK_SIZE,
    TEXT_CHUNK_OVERLAP, VECTOR_DB_SEARCH_RESULTS, CHROMA_DB_PATH
)

def slugify(value: str) -> str:
    """
    Chuyển đổi chuỗi Unicode (bao gồm Tiếng Việt) thành một chuỗi an toàn
    để dùng làm ID hoặc tên file, tránh lỗi khi tương tác với hệ thống.
    Đây là một hàm cực kỳ quan trọng để đảm bảo tính ổn định của hệ thống.

    Args:
        value (str): Chuỗi đầu vào cần xử lý.

    Returns:
        str: Chuỗi an toàn, đã được chuyển thành chữ thường, không dấu,
             và thay thế khoảng trắng bằng dấu gạch ngang.
    """
    value = normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value

# --- Khởi tạo các dịch vụ toàn cục mà ứng dụng sẽ sử dụng ---
# Cấu hình API key cho thư viện của Google.
genai.configure(api_key=GEMINI_API_KEY)
# Khởi tạo client kết nối tới ChromaDB, dữ liệu sẽ được lưu trên đĩa.
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
# Khởi tạo mô hình ngôn ngữ chính sẽ được sử dụng cho các tác vụ AI.
generative_model = genai.GenerativeModel(GENERATIVE_MODEL_NAME)

class DocumentProcessor:
    """
    Lớp này chịu trách nhiệm duy nhất cho việc trích xuất văn bản thô
    từ các nguồn khác nhau (PDF, DOCX, URL, YouTube, Text).
    Mỗi phương thức đều có error handling riêng để đảm bảo sự ổn định.
    """
    def extract_text(self, source_type: str, source_data: any) -> tuple[str | None, str]:
        """
        Phương thức chính để trích xuất văn bản.

        Args:
            source_type (str): Loại nguồn ('pdf', 'docx', 'url', 'text').
            source_data (any): Dữ liệu nguồn (file object, chuỗi URL, chuỗi văn bản).

        Returns:
            tuple[str | None, str]: Một tuple chứa (nội dung văn bản, tên nguồn đã được xử lý).
                                     Trả về (None, thông báo lỗi) nếu thất bại.
        """
        try:
            if not source_data:
                return None, "Nguồn dữ liệu rỗng."
            
            if source_type == 'pdf':
                safe_name = slugify(source_data.name)
                reader = PdfReader(source_data)
                text = "".join(page.extract_text() + "\n" for page in reader.pages if page.extract_text())
                return text, safe_name
            
            elif source_type == 'docx':
                safe_name = slugify(source_data.name)
                doc = docx.Document(source_data)
                text = "\n".join([para.text for para in doc.paragraphs if para.text])
                return text, safe_name
            
            elif source_type == 'text':
                return source_data, "pasted-text"
                
            elif source_type == 'url':
                if "youtube.com/watch?v=" in source_data or "youtu.be/" in source_data:
                    video_id = source_data.split("v=")[-1].split('&')[0]
                    if "/" in video_id: video_id = video_id.split("/")[-1]
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['vi', 'en'])
                    text = " ".join([item['text'] for item in transcript_list])
                    return text, f"youtube-{video_id}"

                response = requests.get(source_data, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                text = ' '.join(t.get_text(separator=' ', strip=True) for t in soup.find_all(text=True))
                title = slugify(soup.title.string.strip() if soup.title else source_data)
                return text, title
                
        except Exception as e:
            return None, f"Lỗi khi xử lý nguồn: {str(e)}"
        return None, "Loại nguồn không được hỗ trợ."

class CourseManager:
    """
    Lớp này quản lý việc tương tác với database vector (ChromaDB).
    Nó xử lý việc tạo, xóa, thêm tài liệu, và liệt kê các khóa học.
    Đây là lớp trừu tượng hóa việc giao tiếp với cơ sở dữ liệu.
    """
    def __init__(self, client: chromadb.Client):
        self.client = client

    def list_courses(self) -> list[dict]:
        """Liệt kê tất cả các khóa học, trả về danh sách các dictionary."""
        collections = self.client.list_collections()
        course_list = []
        for col in collections:
            name = col.metadata.get("display_name", col.name) if col.metadata else col.name
            course_list.append({"id": col.name, "name": name})
        return course_list

    def get_course_details(self, course_id: str) -> dict | None:
        """Lấy chi tiết về một khóa học cụ thể."""
        try:
            collection = self.client.get_collection(name=course_id)
            count = collection.count()
            return {"name": collection.name, "count": count}
        except ValueError:
            return None

    def get_or_create_course_collection(self, course_id: str, display_name: str) -> chromadb.Collection:
        """Tạo một khóa học mới hoặc lấy khóa học đã có, lưu tên gốc vào metadata."""
        return self.client.get_or_create_collection(name=course_id, metadata={"display_name": display_name})
    
    def delete_course(self, course_id: str) -> tuple[bool, str]:
        """Xóa một khóa học khỏi database."""
        try:
            self.client.delete_collection(name=course_id)
            return True, f"Đã xóa thành công khóa học."
        except ValueError:
            return False, f"Lỗi: Không tìm thấy khóa học để xóa."
        except Exception as e:
            return False, f"Lỗi không xác định khi xóa: {e}"

    def add_document(self, course_id: str, document_text: str, source_name: str) -> int:
        """Thêm một tài liệu đã được xử lý vào một khóa học."""
        collection = self.client.get_collection(name=course_id)
        chunks = self._split_text(document_text)
        if not chunks: return 0
        doc_ids = [f"{course_id}-{source_name}-{i}-{int(time.time() * 1000)}" for i in range(len(chunks))]
        collection.add(documents=chunks, ids=doc_ids)
        return len(chunks)

    def _split_text(self, text: str) -> list[str]:
        """Hàm nội bộ để chia nhỏ văn bản thành các chunks."""
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokens = tokenizer.encode(text)
        chunks = []
        for i in range(0, len(tokens), TEXT_CHUNK_SIZE - TEXT_CHUNK_OVERLAP):
            chunks.append(tokenizer.decode(tokens[i:i + TEXT_CHUNK_SIZE]))
        return chunks

class AIService:
    """
    Lớp này chứa tất cả các logic nghiệp vụ liên quan đến AI.
    Mỗi chức năng là một phương thức riêng biệt với prompt được thiết kế cẩn thận.
    """
    def __init__(self, course_manager: CourseManager):
        self.course_manager = course_manager

    def _get_full_context(self, course_id: str, max_chunks: int = 20) -> str | None:
        """Hàm nội bộ để lấy toàn bộ hoặc một phần lớn ngữ cảnh của khóa học."""
        try:
            collection = self.course_manager.client.get_collection(name=course_id)
            if collection.count() == 0: return None
            documents = collection.get(limit=min(collection.count(), max_chunks))
            return "\n---\n".join(documents['documents'])
        except Exception:
            return None

    def get_chat_answer(self, course_id: str, question: str) -> str:
        """Hàm trả lời câu hỏi RAG, đã được tối ưu và sửa lỗi logic."""
        try:
            collection = self.course_manager.client.get_collection(name=course_id)
            if collection.count() == 0:
                return "Tôi không tìm thấy bất kỳ tài liệu nào trong khóa học này. Vui lòng thêm tài liệu và thử lại."
            
            results = collection.query(query_texts=[question], n_results=VECTOR_DB_SEARCH_RESULTS)
            if not results['documents'] or not results['documents'][0]:
                return "Tôi không tìm thấy thông tin liên quan trong tài liệu để trả lời câu hỏi của bạn."

            context = "\n---\n".join(results['documents'][0])
            prompt = f"""Bạn là PNote, trợ lý AI chuyên gia. Trả lời câu hỏi DỰA HOÀN TOÀN vào "NGỮ CẢNH" sau. QUY TẮC: 1. CHỈ dùng thông tin từ "NGỮ CẢNH". Nếu không có, nói: "Tôi không tìm thấy thông tin này trong tài liệu." 2. Trả lời trực tiếp, súc tích, chuyên nghiệp. 3. Không đưa ra ý kiến cá nhân. NGỮ CẢNH: --- {context} --- CÂU HỎI: "{question}" """
            response = generative_model.generate_content(prompt)
            return response.text
        except ValueError:
            return "Lỗi: Không tìm thấy khóa học này. Có thể nó đã bị xóa hoặc chưa được tạo."
        except Exception as e:
            return f"Đã xảy ra một lỗi không mong muốn khi truy vấn: {str(e)}"

    def summarize_course(self, course_id: str) -> str:
        """Tạo bản tóm tắt cho toàn bộ khóa học."""
        context = self._get_full_context(course_id)
        if not context:
            return "Không có đủ dữ liệu để tạo tóm tắt. Vui lòng thêm tài liệu."
        
        prompt = f"""Dựa vào toàn bộ "NGỮ CẢNH" dưới đây, hãy viết một bản tóm tắt súc tích, gãy gọn, và đi vào trọng tâm. Chia câu trả lời thành các gạch đầu dòng với các ý chính. NGỮ CẢNH: --- {context} --- TÓM TẮT:"""
        try:
            response = generative_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Lỗi khi tóm tắt: {e}"

    def generate_quiz(self, course_id: str, num_questions: int = 5) -> list | str:
        """Tạo câu hỏi trắc nghiệm từ nội dung khóa học."""
        context = self._get_full_context(course_id)
        if not context:
            return "Không có đủ dữ liệu để tạo câu hỏi. Vui lòng thêm tài liệu."
            
        prompt = f"""Bạn là một chuyên gia tạo câu hỏi thi. Dựa vào "NGỮ CẢNH", hãy tạo ra {num_questions} câu hỏi trắc nghiệm (MCQ) để kiểm tra kiến thức. Trả lời dưới dạng một danh sách JSON. Mỗi đối tượng JSON phải có các key: "question", "options" (một danh sách 4 lựa chọn), và "answer" (đáp án đúng). NGỮ CẢNH: --- {context} --- DANH SÁCH JSON:"""
        try:
            response = generative_model.generate_content(prompt)
            json_string = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(json_string)
        except Exception:
            return "Rất tiếc, tôi không thể tạo câu hỏi từ tài liệu này. Vui lòng thử lại với tài liệu khác."

    def extract_keywords(self, course_id: str, num_keywords: int = 10) -> list | str:
        """Trích xuất các từ khóa/khái niệm quan trọng."""
        context = self._get_full_context(course_id)
        if not context:
            return "Không có đủ dữ liệu để trích xuất từ khóa. Vui lòng thêm tài liệu."
        
        prompt = f"""Dựa vào "NGỮ CẢNH", hãy xác định {num_keywords} từ khóa hoặc khái niệm quan trọng nhất. Liệt kê chúng dưới dạng danh sách, mỗi từ khóa trên một dòng. NGỮ CẢNH: --- {context} --- TỪ KHÓA:"""
        try:
            response = generative_model.generate_content(prompt)
            keywords = [line.strip().replace("-", "").strip() for line in response.text.split("\n") if line.strip()]
            return keywords
        except Exception as e:
            return f"Lỗi khi trích xuất từ khóa: {e}"

    def translate_text(self, text_to_translate: str, target_language: str = "Tiếng Việt") -> str:
        """Dịch văn bản bằng Gemini."""
        if not text_to_translate: return ""
        prompt = f"Translate the following text to {target_language}. Respond with only the translated text, no additional explanations:\n\n{text_to_translate}"
        try:
            response = generative_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Lỗi dịch thuật: {e}"

# Khởi tạo các instance của services để các module khác import
document_processor_service = DocumentProcessor()
course_manager_service = CourseManager(chroma_client)
ai_service = AIService(course_manager_service)
