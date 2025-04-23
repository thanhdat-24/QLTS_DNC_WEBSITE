import os
import base64
import hashlib
from dotenv import load_dotenv

# Tải biến môi trường từ file .env (nếu có)
load_dotenv()

class Config:
    """Cấu hình ứng dụng Flask"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
    
    # Cấu hình cổng (mới thêm)
    PORT = int(os.getenv('PORT', 5000))
    
    # Cấu hình Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://hoybfwnugefnpctgghha.supabase.co')
    SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhveWJmd251Z2VmbnBjdGdnaGhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxMDQ4OTEsImV4cCI6MjA1OTY4MDg5MX0.KxNfiOUFXHGgqZf3b3xOk6BR4sllMZG_-W-y_OPUwCI')
    
    # Khóa mã hóa URL
    URL_ENCRYPTION_KEY = os.getenv('URL_ENCRYPTION_KEY')
    if not URL_ENCRYPTION_KEY:
        # Tạo khóa mã hóa từ SECRET_KEY nếu không được cung cấp
        key_bytes = hashlib.sha256(SECRET_KEY.encode()).digest()
        URL_ENCRYPTION_KEY = base64.urlsafe_b64encode(key_bytes)
    
# Cấu hình khác
ITEMS_PER_PAGE = 12  # Thay đổi từ 10 thành 12
USE_ENCRYPTED_URLS = os.getenv('USE_ENCRYPTED_URLS', 'True').lower() in ('true', '1', 't')