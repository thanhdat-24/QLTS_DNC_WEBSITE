from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import AuthService, login_required
from datetime import datetime

# Tạo Blueprint cho các route liên quan đến xác thực
auth_routes = Blueprint('auth_routes', __name__)
auth_service = AuthService()

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    """Trang đăng nhập"""
    # Nếu người dùng đã đăng nhập, chuyển hướng đến trang chủ
    if auth_service.is_authenticated():
        return redirect(url_for('asset_routes.index'))
    
    # Xử lý khi form được submit
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Vui lòng nhập đầy đủ thông tin đăng nhập', 'error')
            return render_template('auth/login.html')
        
        # Kiểm tra đăng nhập
        user = auth_service.login(username, password)
        
        if user:
            # Lưu thông tin người dùng vào session
            session['user'] = user
            
            # Kiểm tra redirect URL từ query string (nếu có)
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('asset_routes.index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác', 'error')
    
    return render_template('auth/login.html')

@auth_routes.route('/logout')
def logout():
    """Đăng xuất người dùng"""
    auth_service.logout()
    flash('Đăng xuất thành công!', 'success')
    return redirect(url_for('auth_routes.login'))

@auth_routes.route('/profile')
@login_required
def profile():
    """Trang thông tin cá nhân"""
    user = auth_service.get_current_user()
    return render_template('auth/profile.html', user=user)