import base64
import hashlib
from cryptography.fernet import Fernet
import hmac
import secrets
from flask import current_app

class URLEncryption:
    """
    Lớp cung cấp các phương thức để mã hóa và giải mã URL trong ứng dụng.
    Sử dụng Fernet để mã hóa đảm bảo tính bảo mật và tính xác thực.
    """
    
    @staticmethod
    def generate_key():
        """Tạo khóa mã hóa mới"""
        return Fernet.generate_key()
    
    @staticmethod
    def get_encryption_key():
        """Lấy khóa mã hóa từ cấu hình ứng dụng hoặc tạo mới"""
        # Cố gắng lấy khóa từ config
        key = current_app.config.get('URL_ENCRYPTION_KEY')
        
        if not key:
            # Nếu không có khóa, tạo khóa mới từ SECRET_KEY
            secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')
            key = base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())
        
        return key
    
    @staticmethod
    def encrypt_url_path(path):
        """
        Mã hóa đường dẫn URL
        
        Args:
            path: Đường dẫn cần mã hóa, ví dụ: '/assets/201'
            
        Returns:
            Chuỗi mã hóa an toàn có thể sử dụng trong URL
        """
        if not path:
            return ""
        
        try:
            # Lấy khóa mã hóa
            key = URLEncryption.get_encryption_key()
            cipher = Fernet(key)
            
            # Mã hóa đường dẫn
            encrypted_data = cipher.encrypt(path.encode())
            
            # Chuyển đổi kết quả sang base64url để an toàn cho URL
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            # Log lỗi nếu cần
            print(f"Error encrypting URL path: {e}")
            # Trả về path gốc nếu có lỗi xảy ra
            return path
    
    @staticmethod
    def decrypt_url_path(encrypted_path):
        """
        Giải mã đường dẫn URL đã mã hóa
        
        Args:
            encrypted_path: Chuỗi mã hóa
            
        Returns:
            Đường dẫn gốc, hoặc None nếu giải mã thất bại
        """
        if not encrypted_path:
            return None
        
        try:
            # Lấy khóa mã hóa
            key = URLEncryption.get_encryption_key()
            cipher = Fernet(key)
            
            # Chuyển đổi chuỗi base64url thành dữ liệu nhị phân
            encrypted_data = base64.urlsafe_b64decode(encrypted_path)
            
            # Giải mã
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # Trả về đường dẫn gốc
            return decrypted_data.decode()
        except Exception as e:
            # Log lỗi nếu cần
            print(f"Error decrypting URL path: {e}")
            return None
    
    # Phương thức ngắn gọn hơn với khóa cố định cho URL
    @staticmethod
    def encode_asset_id(asset_id):
        """
        Mã hóa ID tài sản thành chuỗi an toàn cho URL
        
        Args:
            asset_id: ID tài sản cần mã hóa
            
        Returns:
            Chuỗi mã hóa an toàn cho URL
        """
        try:
            # Chuyển asset_id thành chuỗi
            asset_id_str = str(asset_id)
            
            # Lấy khóa từ cấu hình
            key = URLEncryption.get_encryption_key()
            cipher = Fernet(key)
            
            # Mã hóa
            encrypted = cipher.encrypt(asset_id_str.encode())
            
            # Chuyển đổi sang base64url
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Error encoding asset ID: {e}")
            # Trả về ID gốc (dưới dạng chuỗi) nếu có lỗi
            return str(asset_id)

    @staticmethod
    def decode_asset_id(encoded_id):
        """
        Giải mã chuỗi thành ID tài sản
        
        Args:
            encoded_id: Chuỗi mã hóa ID tài sản
            
        Returns:
            ID tài sản gốc (dạng số), hoặc None nếu giải mã thất bại
        """
        try:
            # Lấy khóa từ cấu hình
            key = URLEncryption.get_encryption_key()
            cipher = Fernet(key)
            
            # Chuyển đổi chuỗi base64url thành dữ liệu nhị phân
            encrypted_data = base64.urlsafe_b64decode(encoded_id)
            
            # Giải mã
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # Chuyển đổi thành số nguyên
            return int(decrypted_data.decode())
        except Exception as e:
            print(f"Error decoding asset ID: {e}")
            return None