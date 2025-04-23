from flask import Blueprint, jsonify, request, render_template
from services.notification_service import NotificationService
from services.auth_service import login_required, AuthService
from datetime import datetime

# Tạo Blueprint cho các route liên quan đến thông báo
notification_routes = Blueprint('notification_routes', __name__)
notification_service = NotificationService()
auth_service = AuthService()

@notification_routes.route('/api/notifications')
@login_required
def get_notifications():
    """API lấy danh sách thông báo của người dùng hiện tại"""
    # Lấy tham số từ query string
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    include_read = request.args.get('include_read', 'false').lower() == 'true'
    
    # Lấy ID của người dùng hiện tại
    user = auth_service.get_current_user()
    if not user:
        return jsonify({'error': 'Không tìm thấy thông tin người dùng'}), 401
    
    user_id = user.get('ma_tk')
    
    # Lấy danh sách thông báo
    notifications, unread_count = notification_service.get_notifications(
        user_id=user_id,
        limit=limit,
        offset=offset,
        include_read=include_read
    )
    
    return jsonify({
        'notifications': notifications,
        'unread_count': unread_count,
        'total': len(notifications)
    })

@notification_routes.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    """API đánh dấu thông báo là đã đọc"""
    # Lấy ID của người dùng hiện tại
    user = auth_service.get_current_user()
    if not user:
        return jsonify({'error': 'Không tìm thấy thông tin người dùng'}), 401
    
    # Kiểm tra xem thông báo có thuộc về người dùng không
    notification = notification_service.get_notification_by_id(notification_id)
    if not notification or notification.get('ma_tk') != user.get('ma_tk'):
        return jsonify({'error': 'Không tìm thấy thông báo'}), 404
    
    # Đánh dấu là đã đọc
    result = notification_service.mark_as_read(notification_id)
    
    return jsonify({
        'success': True,
        'message': 'Đã đánh dấu thông báo là đã đọc'
    })

@notification_routes.route('/api/notifications/read-all', methods=['PUT'])
@login_required
def mark_all_notifications_read():
    """API đánh dấu tất cả thông báo là đã đọc"""
    # Lấy ID của người dùng hiện tại
    user = auth_service.get_current_user()
    if not user:
        return jsonify({'error': 'Không tìm thấy thông tin người dùng'}), 401
    
    user_id = user.get('ma_tk')
    
    # Đánh dấu tất cả là đã đọc
    result = notification_service.mark_all_as_read(user_id)
    
    return jsonify({
        'success': True,
        'message': 'Đã đánh dấu tất cả thông báo là đã đọc'
    })

@notification_routes.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """API xóa thông báo"""
    # Lấy ID của người dùng hiện tại
    user = auth_service.get_current_user()
    if not user:
        return jsonify({'error': 'Không tìm thấy thông tin người dùng'}), 401
    
    # Kiểm tra xem thông báo có thuộc về người dùng không
    notification = notification_service.get_notification_by_id(notification_id)
    if not notification or notification.get('ma_tk') != user.get('ma_tk'):
        return jsonify({'error': 'Không tìm thấy thông báo'}), 404
    
    # Xóa thông báo
    result = notification_service.delete_notification(notification_id)
    
    return jsonify({
        'success': True,
        'message': 'Đã xóa thông báo'
    })

@notification_routes.route('/api/notifications/count')
@login_required
def get_unread_notification_count():
    """API lấy số lượng thông báo chưa đọc"""
    # Lấy ID của người dùng hiện tại
    user = auth_service.get_current_user()
    if not user:
        return jsonify({'error': 'Không tìm thấy thông tin người dùng'}), 401
    
    user_id = user.get('ma_tk')
    
    # Lấy số thông báo chưa đọc
    _, unread_count = notification_service.get_notifications(
        user_id=user_id,
        limit=1,  # Chỉ cần lấy 1 bản ghi để đếm
        include_read=False
    )
    
    return jsonify({
        'unread_count': unread_count
    })

# Thêm route để tạo thông báo (thường chỉ dùng cho testing hoặc admin)
@notification_routes.route('/api/notifications', methods=['POST'])
@login_required
def create_notification():
    """API tạo thông báo mới (chỉ dùng cho testing hoặc admin)"""
    # Lấy dữ liệu từ request
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dữ liệu không hợp lệ'}), 400
    
    # Lấy thông tin người dùng hiện tại
    user = auth_service.get_current_user()
    if not user:
        return jsonify({'error': 'Không tìm thấy thông tin người dùng'}), 401
    
    user_id = user.get('ma_tk')
    
    # Kiểm tra quyền admin nếu cần
    # is_admin = auth_service.has_role('admin')
    # if not is_admin:
    #     return jsonify({'error': 'Không có quyền thực hiện hành động này'}), 403
    
    # Lấy các trường cần thiết
    message = data.get('message')
    type = data.get('type', 'info')
    reference_type = data.get('reference_type')
    reference_id = data.get('reference_id')
    link = data.get('link')
    
    if not message:
        return jsonify({'error': 'Thiếu nội dung thông báo'}), 400
    
    # Tạo thông báo
    result = notification_service.create_notification(
        user_id=user_id,
        type=type,
        message=message,
        reference_type=reference_type,
        reference_id=reference_id,
        link=link
    )
    
    return jsonify({
        'success': True,
        'data': result,
        'message': 'Đã tạo thông báo mới'
    })

# Thêm route để hiển thị trang thông báo
@notification_routes.route('/notifications')
@login_required
def notifications_page():
    """Trang hiển thị danh sách thông báo"""
    # Lấy tham số từ query string
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Số thông báo mỗi trang
    filter_type = request.args.get('filter', 'all')
    
    # Lấy thông tin người dùng hiện tại
    user = auth_service.get_current_user()
    user_id = user.get('ma_tk')
    
    # Xác định có lấy thông báo đã đọc không
    include_read = filter_type != 'unread'
    
    # Tính offset dựa trên trang
    offset = (page - 1) * per_page
    
    # Lấy danh sách thông báo
    notifications, unread_count = notification_service.get_notifications(
        user_id=user_id,
        limit=per_page,
        offset=offset,
        include_read=include_read
    )
    
    # Lấy tổng số thông báo cho phân trang
    if filter_type == 'all':
        # Đếm tổng số thông báo
        all_notifications, _ = notification_service.get_notifications(
            user_id=user_id,
            limit=1,
            include_read=True,
            count_only=True
        )
        total_count = all_notifications
    elif filter_type == 'unread':
        # Chỉ đếm số thông báo chưa đọc
        total_count = unread_count
    elif filter_type == 'read':
        # Đếm số thông báo đã đọc
        all_notifications, _ = notification_service.get_notifications(
            user_id=user_id,
            limit=1,
            include_read=True,
            count_only=True
        )
        read_notifications, _ = notification_service.get_notifications(
            user_id=user_id,
            limit=1,
            include_read=False,
            count_only=True
        )
        total_count = all_notifications - read_notifications
        
        # Lọc thông báo đã đọc
        notifications = [n for n in notifications if n.get('da_doc')]
    
    # Tính toán thông tin phân trang
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    pagination = {
        'page': page,
        'total': total_count,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'per_page': per_page
    }
    
    # Helper functions for template
    def get_notification_icon_class(type):
        """Lấy class cho icon thông báo"""
        if type == 'info':
            return 'info-icon'
        elif type == 'update':
            return 'update-icon'
        elif type == 'warning':
            return 'warning-icon'
        elif type == 'error':
            return 'error-icon'
        return 'info-icon'
    
    def get_notification_icon(type):
        """Lấy icon cho loại thông báo"""
        if type == 'info':
            return 'fas fa-info-circle'
        elif type == 'update':
            return 'fas fa-sync-alt'
        elif type == 'warning':
            return 'fas fa-exclamation-triangle'
        elif type == 'error':
            return 'fas fa-times-circle'
        return 'fas fa-info-circle'
    
    def format_notification_time(timestamp):
        """Format thời gian thông báo"""
        if not timestamp:
            return ''
        
        try:
            timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now()
            diff = (now - timestamp_dt).total_seconds()
            
            if diff < 60:
                return 'Vừa xong'
            elif diff < 3600:
                minutes = int(diff // 60)
                return f'{minutes} phút trước'
            elif diff < 86400:
                hours = int(diff // 3600)
                return f'{hours} giờ trước'
            elif diff < 604800:  # 7 ngày
                days = int(diff // 86400)
                return f'{days} ngày trước'
            else:
                return timestamp_dt.strftime('%d/%m/%Y %H:%M')
        except (ValueError, TypeError):
            return timestamp
    
    return render_template(
        'notifications.html',
        notifications=notifications,
        pagination=pagination,
        filter=filter_type,
        get_notification_icon_class=get_notification_icon_class,
        get_notification_icon=get_notification_icon,
        format_notification_time=format_notification_time
    )