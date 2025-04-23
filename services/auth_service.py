from datetime import datetime, timedelta
import hashlib
import jwt
from functools import wraps
from flask import request, redirect, url_for, session, flash
from services.supabase_service import SupabaseService

class AuthService:
    """
    Dịch vụ xác thực người dùng
    """
    def __init__(self):
        self.supabase = SupabaseService()
        self.secret_key = "your_jwt_secret_key_change_in_production"  # Thay đổi trong môi trường thực tế
        self.token_expire = 24 * 60 * 60  # 24 giờ (tính bằng giây)
    
    # def hash_password(self, password):
    #     """
    #     Mã hóa mật khẩu bằng SHA-256
        
    #     Args:
    #         password: Mật khẩu gốc
            
    #     Returns:
    #         Mật khẩu đã mã hóa
    #     """
    #     return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, provided_password, stored_password):
        """
        Xác minh mật khẩu
    
        Args:
            provided_password: Mật khẩu người dùng nhập
            stored_password: Mật khẩu được lưu trong DB
        
        Returns:
            True nếu mật khẩu đúng, False nếu sai
        """
        # So sánh trực tiếp mật khẩu mà không mã hóa
        return provided_password == stored_password
    
    def login(self, username, password):
        """
        Đăng nhập người dùng
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu
            
        Returns:
            User info nếu đăng nhập thành công, None nếu thất bại
        """
        # Lấy thông tin tài khoản từ Supabase
        response = self.supabase.client.table('taikhoan') \
            .select('*, loaitaikhoan:ma_loai_tk(ten_loai_tk), nhanvien:ma_nv(*)') \
            .eq('ten_tai_khoan', username) \
            .execute()
            
        # Kiểm tra xem có tìm thấy tài khoản không
        if not response.data or len(response.data) == 0:
            return None
        
        account = response.data[0]
        
        # Kiểm tra mật khẩu
        if not self.verify_password(password, account['mat_khau']):
            return None
        
        # Tạo thông tin user từ dữ liệu tài khoản
        user_info = {
            'ma_tk': account['ma_tk'],
            'ten_tai_khoan': account['ten_tai_khoan'],
            'ma_loai_tk': account['ma_loai_tk'],
            'ten_loai_tk': account['loaitaikhoan']['ten_loai_tk'] if account.get('loaitaikhoan') else None,
            'ma_nv': account['ma_nv'],
            'ten_nv': account['nhanvien']['ten_nv'] if account.get('nhanvien') else None,
        }
        
        # Tạo JWT token
        token = self.generate_token(user_info)
        user_info['token'] = token
        
        return user_info
    
    def generate_token(self, user_data):
        """
        Tạo JWT token
        
        Args:
            user_data: Dữ liệu người dùng để lưu vào token
            
        Returns:
            JWT token
        """
        payload = {
            'user_id': user_data['ma_tk'],
            'username': user_data['ten_tai_khoan'],
            'role': user_data['ma_loai_tk'],
            'exp': datetime.utcnow() + timedelta(seconds=self.token_expire)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        """
        Xác minh JWT token
        
        Args:
            token: JWT token cần xác minh
            
        Returns:
            Dữ liệu người dùng nếu token hợp lệ, None nếu không
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            # Token đã hết hạn
            return None
        except jwt.InvalidTokenError:
            # Token không hợp lệ
            return None
    
    def get_current_user(self):
        """
        Lấy thông tin người dùng hiện tại từ session
        
        Returns:
            Thông tin người dùng hoặc None nếu chưa đăng nhập
        """
        if 'user' not in session:
            return None
        
        return session['user']
    
    def is_authenticated(self):
        """
        Kiểm tra người dùng đã đăng nhập chưa
        
        Returns:
            True nếu đã đăng nhập, False nếu chưa
        """
        return 'user' in session and session['user'] is not None
    
    def has_role(self, required_roles):
        """
        Kiểm tra người dùng có vai trò cần thiết không
        
        Args:
            required_roles: Danh sách các role ID cần thiết
            
        Returns:
            True nếu có quyền, False nếu không
        """
        if not self.is_authenticated():
            return False
        
        user_role = session['user'].get('ma_loai_tk')
        
        if isinstance(required_roles, list):
            return user_role in required_roles
        return user_role == required_roles
    
    def logout(self):
        """
        Đăng xuất người dùng
        """
        if 'user' in session:
            session.pop('user', None)


def login_required(func):
    """
    Decorator để yêu cầu đăng nhập trước khi truy cập route
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        auth_service = AuthService()
        if not auth_service.is_authenticated():
            flash('Bạn cần đăng nhập để truy cập trang này', 'warning')
            return redirect(url_for('auth_routes.login', next=request.url))
        return func(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """
    Decorator để yêu cầu vai trò cụ thể trước khi truy cập route
    
    Args:
        roles: Vai trò cần thiết (ID hoặc danh sách các ID)
    """
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            auth_service = AuthService()
            if not auth_service.is_authenticated():
                flash('Bạn cần đăng nhập để truy cập trang này', 'warning')
                return redirect(url_for('auth_routes.login', next=request.url))
            
            if not auth_service.has_role(roles):
                flash('Bạn không có quyền truy cập trang này', 'error')
                return redirect(url_for('asset_routes.index'))
                
            return func(*args, **kwargs)
        return decorated_function
    return decorator