from flask import Flask, render_template, session, redirect, url_for, request
from routes.asset_routes import asset_routes
from routes.auth_routes import auth_routes
from services.auth_service import AuthService
from config import Config
import os
import socket
from routes.notification_routes import notification_routes

def create_app(config_class=Config):
    """Tạo và cấu hình ứng dụng Flask"""
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )
    
    # Tải cấu hình
    app.config.from_object(config_class)
    app.register_blueprint(notification_routes)# Đăng ký blueprint mới
    # Đăng ký blueprint
    app.register_blueprint(asset_routes)
    app.register_blueprint(auth_routes, url_prefix='/auth')
    
    # Khởi tạo dịch vụ xác thực
    auth_service = AuthService()
    
    # Middleware để kiểm tra xác thực trước mỗi request
    @app.before_request
    def check_auth():
        # Danh sách các route không cần xác thực
        public_routes = [
            '/auth/login',
            '/static/',
            '/favicon.ico'
        ]
        
        # Kiểm tra URL hiện tại
        for route in public_routes:
            if request.path.startswith(route):
                return None
        
        # Kiểm tra đăng nhập
        if not auth_service.is_authenticated():
            return redirect(url_for('auth_routes.login', next=request.full_path))
    
    # Biến toàn cục cho template
    @app.context_processor
    def inject_user():
        return {
            'current_user': auth_service.get_current_user(),
            'is_authenticated': auth_service.is_authenticated()
        }
    
    # Xử lý lỗi 404
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    # Xử lý lỗi 500
    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500
    
    return app

# ------------------- MAIN -------------------

if __name__ == '__main__':
    app = create_app()

    # Lấy địa chỉ IP hiện tại
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # In ra các đường dẫn truy cập
    print("\nỨng dụng Flask đang chạy tại:")
    print(f" * http://127.0.0.1:8080 (Localhost)")
    print(f" * http://{local_ip}:8080 (Nội bộ LAN)")
    print(" * http://<IP CÔNG CỘNG>:8080 (Từ bên ngoài - nếu port forwarding thành công)")

    # Chạy ứng dụng Flask để có thể truy cập từ LAN & Internet
    app.run(host='0.0.0.0', port=8080, debug=True)