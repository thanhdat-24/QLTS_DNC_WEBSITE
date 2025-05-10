from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file
from services.asset_service import AssetService
from services.auth_service import login_required, role_required, AuthService
from services.url_encryption import URLEncryption
from datetime import datetime, date
from services.notification_service import NotificationService
from services.supabase_service import SupabaseService

# Tạo Blueprint cho các route liên quan đến tài sản
asset_routes = Blueprint('asset_routes', __name__)
asset_service = AssetService()
auth_service = AuthService()
notification_service = NotificationService()

@asset_routes.route('/')
@login_required
def index():
    """Trang chủ với danh sách tài sản"""
    # Lấy tham số từ query string
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    group = request.args.get('group', 'all')
    status = request.args.get('status', 'all')
    
    # Lấy danh sách tài sản và thông tin phân trang
    assets, pagination = asset_service.get_assets(
        page=page,
        search=search,
        group=group,
        status=status,
        limit=12
    )
    
    # Lấy thống kê tài sản
    stats = asset_service.get_asset_stats()
    
    # Lấy danh sách nhóm tài sản để hiển thị filter
    groups = asset_service.get_groups()
    
    return render_template(
        'index.html',
        assets=assets,
        pagination=pagination,
        stats=stats,
        groups=groups,
        search=search,
        selected_group=group,
        selected_status=status
    )

@asset_routes.route('/assets/<int:asset_id>')
@login_required
def asset_detail(asset_id):
    """Chi tiết tài sản theo ID"""
    # Kiểm tra xem có sử dụng URL mã hóa không
    if current_app.config.get('USE_ENCRYPTED_URLS', False):
        # Nếu sử dụng mã hóa, chuyển hướng đến URL đã mã hóa
        encoded_id = URLEncryption.encode_asset_id(asset_id)
        return redirect(url_for('asset_routes.encrypted_asset_detail', encoded_id=encoded_id))
    
    asset = asset_service.get_asset_detail(asset_id)
    
    if not asset:
        flash('Không tìm thấy tài sản', 'error')
        return redirect(url_for('asset_routes.index'))
    
    # Lấy cả hai loại thông số
    group_specs, specific_specs = asset_service.get_asset_specifications(asset_id)
    
    # Xác định tab active từ query string hoặc mặc định
    active_tab = request.args.get('tab', 'specific')
    
    return render_template(
        'assets/detail.html',
        asset=asset,
        group_specs=group_specs,
        specific_specs=specific_specs,
        active_tab=active_tab
    )

@asset_routes.route('/a/<path:encoded_id>')
@login_required
def encrypted_asset_detail(encoded_id):
    """Chi tiết tài sản với ID đã mã hóa"""
    # Giải mã ID tài sản
    try:
        asset_id = URLEncryption.decode_asset_id(encoded_id)
        if asset_id is None:
            flash('Đường dẫn không hợp lệ', 'error')
            return redirect(url_for('asset_routes.index'))
    except Exception as e:
        flash('Đường dẫn không hợp lệ', 'error')
        return redirect(url_for('asset_routes.index'))
    
    # Lấy thông tin tài sản
    asset = asset_service.get_asset_detail(asset_id)
    
    if not asset:
        flash('Không tìm thấy tài sản', 'error')
        return redirect(url_for('asset_routes.index'))
    
    # Lấy cả hai loại thông số
    group_specs, specific_specs = asset_service.get_asset_specifications(asset_id)
    
    # Xác định tab active từ query string hoặc mặc định
    active_tab = request.args.get('tab', 'specific')
    
    return render_template(
        'assets/detail.html',
        asset=asset,
        group_specs=group_specs,
        specific_specs=specific_specs,
        active_tab=active_tab,
        encoded_id=encoded_id
    )

@asset_routes.route('/api/assets')
@login_required
def api_assets():
    """API trả về danh sách tài sản dạng JSON"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', 'all')
    status = request.args.get('status', 'all')
    
    assets, pagination = asset_service.get_assets(
        page=page,
        search=search,
        category=category,
        status=status
    )
    
    # Nếu sử dụng URL mã hóa, thêm trường encoded_id vào mỗi tài sản
    if current_app.config.get('USE_ENCRYPTED_URLS', False):
        for asset in assets:
            asset['encoded_id'] = URLEncryption.encode_asset_id(asset['ma_tai_san'])
    
    return jsonify({
        'assets': assets,
        'pagination': pagination
    })

@asset_routes.route('/api/assets/<int:asset_id>')
@login_required
def api_asset_detail(asset_id):
    """API trả về chi tiết tài sản dạng JSON"""
    asset = asset_service.get_asset_detail(asset_id)
    
    if not asset:
        return jsonify({'error': 'Không tìm thấy tài sản'}), 404
    
    group_specs, specific_specs = asset_service.get_asset_specifications(asset_id)
    
    # Nếu sử dụng URL mã hóa, thêm trường encoded_id
    if current_app.config.get('USE_ENCRYPTED_URLS', False):
        asset['encoded_id'] = URLEncryption.encode_asset_id(asset_id)
    
    return jsonify({
        'asset': asset,
        'group_specs': group_specs,
        'specific_specs': specific_specs
    })

@asset_routes.route('/api/specifications/<int:spec_id>', methods=['PUT'])
@login_required
def api_update_specification(spec_id):
    """API cập nhật thông số kỹ thuật"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dữ liệu không hợp lệ'}), 400
    
    value = data.get('value')
    status = data.get('status')
    
    if not value or not status:
        return jsonify({'error': 'Thiếu thông tin cần thiết'}), 400
    
    # Lấy thông tin thông số hiện tại trước khi cập nhật
    current_spec = asset_service.get_specification_by_id(spec_id)
    if not current_spec:
        return jsonify({'error': 'Không tìm thấy thông số'}), 404
        
    # Lấy thông tin tài sản
    asset = asset_service.get_asset_detail(current_spec['ma_tai_san'])
    
    # Lấy tên thông số kỹ thuật
    spec_name = current_spec.get('thongso', {}).get('ten_thong_so', 'Thông số')
    
    # Lấy người dùng hiện tại
    user = auth_service.get_current_user()
    user_id = user.get('ma_tk')
    
    # Cập nhật thông số
    result = asset_service.update_specification(spec_id, value, status)
    
    # Tạo thông báo về việc cập nhật thông số
    # Tạo thông báo khi giá trị thay đổi
    if value != current_spec.get('gia_tri'):
        notification_service.create_notification(
            user_id=user_id,
            type='update',
            message=f'Cập nhật giá trị thông số "{spec_name}" của tài sản "{asset.get("chitietphieunhap", {}).get("ten_tai_san", "")}"',
            reference_type='thongso_taisan',
            reference_id=spec_id,
            link=f'/assets/{current_spec["ma_tai_san"]}?tab=specific'
        )
    
    # Tạo thông báo khi tình trạng thay đổi
    if status != current_spec.get('tinh_trang'):
        notification_service.create_notification(
            user_id=user_id,
            type='update',
            message=f'Cập nhật tình trạng thông số "{spec_name}" của tài sản "{asset.get("chitietphieunhap", {}).get("ten_tai_san", "")}" thành {status}',
            reference_type='thongso_taisan',
            reference_id=spec_id,
            link=f'/assets/{current_spec["ma_tai_san"]}?tab=specific'
        )
    
    return jsonify({
        'success': True,
        'data': result
    })

@asset_routes.route('/api/assets/<int:asset_id>/specifications/<int:thongso_id>', methods=['PUT'])
@login_required
def api_update_asset_specification(asset_id, thongso_id):
    """API cập nhật thông số kỹ thuật theo ID tài sản và ID thông số"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dữ liệu không hợp lệ'}), 400
    
    value = data.get('value')
    status = data.get('status')
    
    if not value or not status:
        return jsonify({'error': 'Thiếu thông tin cần thiết'}), 400
    
    result = asset_service.add_specification(asset_id, thongso_id, value, status)
    
    return jsonify({
        'success': True,
        'data': result
    })

@asset_routes.route('/api/assets/<int:asset_id>/specifications/add', methods=['POST'])
@login_required
def api_add_specification(asset_id):
    """API thêm thông số kỹ thuật mới"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dữ liệu không hợp lệ'}), 400
    
    thongso_id = data.get('thongso_id')
    value = data.get('value')
    status = data.get('status')
    
    if not thongso_id or not value or not status:
        return jsonify({'error': 'Thiếu thông tin cần thiết'}), 400
    
    try:
        # Lấy thông tin tài sản
        asset = asset_service.get_asset_detail(asset_id)
        if not asset:
            return jsonify({'error': 'Không tìm thấy tài sản'}), 404
            
        # Lấy tên thông số
        thongso = asset_service.get_thongso_by_id(thongso_id)
        spec_name = thongso.get('ten_thong_so', 'Thông số mới')
        
        # Lấy người dùng hiện tại
        user = auth_service.get_current_user()
        user_id = user.get('ma_tk')
        
        # Thêm mới thông số
        result = asset_service.add_specification(asset_id, thongso_id, value, status)
        
        # Tạo thông báo
        notification_service.create_notification(
            user_id=user_id,
            type='info',
            message=f'Thêm thông số "{spec_name}" cho tài sản "{asset.get("chitietphieunhap", {}).get("ten_tai_san", "")}"',
            reference_type='thongso_taisan',
            reference_id=thongso_id,
            link=f'/assets/{asset_id}?tab=specific'
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@asset_routes.route('/api/categories')
@login_required
def api_categories():
    """API trả về danh sách loại tài sản"""
    categories = asset_service.get_categories()
    return jsonify(categories)

@asset_routes.route('/api/groups')
@login_required
def api_groups():
    """API trả về danh sách nhóm tài sản"""
    category_id = request.args.get('category_id', None, type=int)
    groups = asset_service.get_groups(category_id)
    return jsonify(groups)

@asset_routes.route('/qr')
@login_required
def qr_handler():
    """Xử lý yêu cầu từ QR code và chuyển hướng đến trang chi tiết tài sản"""
    # Lấy tham số từ query string
    asset_id = request.args.get('id')
    seri = request.args.get('seri')
    
    # Nếu có ID tài sản, chuyển thẳng đến trang chi tiết
    if asset_id and asset_id.isdigit():
        asset_id_int = int(asset_id)
        
        # Kiểm tra xem có sử dụng URL mã hóa không
        if current_app.config.get('USE_ENCRYPTED_URLS', False):
            encoded_id = URLEncryption.encode_asset_id(asset_id_int)
            return redirect(url_for('asset_routes.encrypted_asset_detail', encoded_id=encoded_id))
        else:
            return redirect(url_for('asset_routes.asset_detail', asset_id=asset_id_int))
    
    # Nếu chỉ có số seri, tìm tài sản dựa trên số seri
    elif seri:
        asset = asset_service.get_asset_by_seri(seri)
        if asset:
            asset_id_int = asset['ma_tai_san']
            
            # Kiểm tra xem có sử dụng URL mã hóa không
            if current_app.config.get('USE_ENCRYPTED_URLS', False):
                encoded_id = URLEncryption.encode_asset_id(asset_id_int)
                return redirect(url_for('asset_routes.encrypted_asset_detail', encoded_id=encoded_id))
            else:
                return redirect(url_for('asset_routes.asset_detail', asset_id=asset_id_int))
    
    # Nếu không tìm thấy, chuyển về trang danh sách với thông báo
    flash('Không tìm thấy tài sản từ mã QR', 'error')
    return redirect(url_for('asset_routes.index'))

@asset_routes.route('/scan')
@login_required
def scan_qr():
    """Trang quét mã QR"""
    return render_template('scan.html')

# Hàm trợ giúp để tạo URL chi tiết tài sản với mã hóa nếu cần
@asset_routes.app_template_filter('asset_url')
def asset_url_filter(asset_id):
    """Filter để tạo URL đến trang chi tiết tài sản dựa trên cấu hình mã hóa"""
    if current_app.config.get('USE_ENCRYPTED_URLS', False):
        encoded_id = URLEncryption.encode_asset_id(asset_id)
        return url_for('asset_routes.encrypted_asset_detail', encoded_id=encoded_id)
    else:
        return url_for('asset_routes.asset_detail', asset_id=asset_id)
    
# Thêm các endpoint API mới vào asset_routes.py

@asset_routes.route('/api/assets/<int:asset_id>', methods=['PUT'])
@login_required
def api_update_asset(asset_id):
    """API cập nhật thông tin tài sản"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Dữ liệu không hợp lệ'}), 400
    
    try:
        # Lấy thông tin hiện tại của tài sản để so sánh sau này
        current_asset = asset_service.get_asset_detail(asset_id)
        if not current_asset:
            return jsonify({'success': False, 'error': 'Không tìm thấy tài sản'}), 404
            
        # Kiểm tra số seri trùng lặp nếu có cập nhật
        if 'so_seri' in data and data['so_seri']:
            # Kiểm tra trong database
            existing_asset = asset_service.get_asset_by_seri(data['so_seri'])
            if existing_asset and str(existing_asset['ma_tai_san']) != str(asset_id):
                return jsonify({'success': False, 'error': 'Số seri đã tồn tại trong hệ thống'}), 400
        
        # Lấy người dùng hiện tại để tạo thông báo
        user = auth_service.get_current_user()
        user_id = user.get('ma_tk')  # Lấy ID người dùng hiện tại
        
        # Cập nhật tài sản
        result = asset_service.update_asset(asset_id, data)
        
        # Kiểm tra các trường được cập nhật và tạo thông báo tương ứng
        asset_name = current_asset.get('chitietphieunhap', {}).get('ten_tai_san', 'Tài sản')
        
        if 'tinh_trang_sp' in data and data['tinh_trang_sp'] != current_asset.get('tinh_trang_sp'):
            notification_service.create_notification(
                user_id=user_id,
                type='update',
                message=f'Cập nhật tình trạng tài sản "{asset_name}" thành {data["tinh_trang_sp"]}',
                reference_type='taisan',
                reference_id=asset_id,
                link=f'/assets/{asset_id}'
            )
        
        if 'so_seri' in data and data['so_seri'] != current_asset.get('so_seri'):
            notification_service.create_notification(
                user_id=user_id,
                type='update',
                message=f'Cập nhật số seri của tài sản "{asset_name}" thành {data["so_seri"]}',
                reference_type='taisan',
                reference_id=asset_id,
                link=f'/assets/{asset_id}'
            )
        
        if 'ngay_su_dung' in data and data['ngay_su_dung'] != current_asset.get('ngay_su_dung'):
            notification_service.create_notification(
                user_id=user_id,
                type='update',
                message=f'Cập nhật ngày sử dụng của tài sản "{asset_name}"',
                reference_type='taisan',
                reference_id=asset_id,
                link=f'/assets/{asset_id}'
            )
        
        if 'han_bh' in data and data['han_bh'] != current_asset.get('han_bh'):
            notification_service.create_notification(
                user_id=user_id,
                type='update',
                message=f'Cập nhật hạn bảo hành của tài sản "{asset_name}"',
                reference_type='taisan',
                reference_id=asset_id,
                link=f'/assets/{asset_id}'
            )
            
            # Kiểm tra hạn bảo hành sắp hết
            try:
                han_bh_date = datetime.fromisoformat(data['han_bh'])
                days_remaining = (han_bh_date - datetime.now()).days
                
                if 0 <= days_remaining <= 30:
                    notification_service.create_notification(
                        user_id=user_id,
                        type='warning',
                        message=f'Tài sản "{asset_name}" sắp hết hạn bảo hành (còn {days_remaining} ngày)',
                        reference_type='taisan',
                        reference_id=asset_id,
                        link=f'/assets/{asset_id}'
                    )
            except (ValueError, TypeError):
                pass  # Bỏ qua nếu có lỗi chuyển đổi ngày tháng
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@asset_routes.route('/api/assets/check-seri')
@login_required
def api_check_seri():
    """API kiểm tra trùng lặp số seri"""
    seri = request.args.get('seri')
    asset_id = request.args.get('asset_id', None)
    
    if not seri:
        return jsonify({'duplicate': False})
    
    # Kiểm tra số seri trong database
    existing_asset = asset_service.get_asset_by_seri(seri)
    
    # Nếu tìm thấy tài sản và không phải là tài sản hiện tại
    if existing_asset and (not asset_id or str(existing_asset['ma_tai_san']) != str(asset_id)):
        return jsonify({'duplicate': True})
    
    return jsonify({'duplicate': False})

# Thêm đoạn mã này vào cuối file asset_routes.py

from services.history_service import HistoryService
history_service = HistoryService()

@asset_routes.route('/api/assets/<int:asset_id>/history')
@login_required
def api_asset_history(asset_id):
    """API trả về lịch sử của tài sản"""
    # Kiểm tra tài sản có tồn tại không
    asset = asset_service.get_asset_detail(asset_id)
    if not asset:
        return jsonify({'success': False, 'error': 'Không tìm thấy tài sản'}), 404
    
    # Lấy lịch sử của tài sản
    history = history_service.get_asset_history(asset_id)
    
    return jsonify({
        'success': True,
        'asset_id': asset_id,
        'asset_name': asset.get('chitietphieunhap', {}).get('ten_tai_san', 'Tài sản'),
        'history': history
    })

@asset_routes.route('/inventory-check')
@login_required
def inventory_check():
    """Trang kiểm kê tài sản"""
    # Lấy danh sách đợt kiểm kê đang diễn ra
    active_inventory_checks = asset_service.get_active_inventory_checks()
    return render_template('inventory/check.html', inventory_checks=active_inventory_checks)

@asset_routes.route('/api/inventory/scan', methods=['POST'])
@login_required
def process_inventory_scan():
    """API xử lý khi quét QR code trong quá trình kiểm kê"""
    data = request.get_json()
    inventory_check_id = data.get('inventory_check_id')
    asset_id = data.get('asset_id')
    seri = data.get('seri')
    room_id = data.get('room_id')
    
    if not all([inventory_check_id, room_id]) or (not asset_id and not seri):
        return jsonify({'error': 'Thiếu thông tin cần thiết'}), 400
        
    try:
        # Tìm tài sản theo ID hoặc số seri
        asset = None
        if asset_id:
            asset = asset_service.get_asset_detail(int(asset_id))
        elif seri:
            asset = asset_service.get_asset_by_seri(seri)
            
        if not asset:
            return jsonify({'error': 'Không tìm thấy tài sản'}), 404
            
        # Xử lý kiểm kê tài sản
        result = asset_service.process_inventory_scan(
            inventory_check_id=inventory_check_id,
            asset_id=asset['ma_tai_san'],
            room_id=room_id
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@asset_routes.route('/api/inventory/summary/<int:inventory_check_id>')
@login_required
def get_inventory_summary(inventory_check_id):
    """API lấy tổng hợp kết quả kiểm kê"""
    summary = asset_service.get_inventory_summary(inventory_check_id)
    return jsonify(summary)

@asset_routes.route('/api/rooms')
@login_required
def get_rooms():
    """API lấy danh sách phòng"""
    try:
        print("Getting rooms from database...") # Debug log
        rooms = asset_service.get_rooms()
        print(f"Successfully retrieved {len(rooms)} rooms") # Debug log
        return jsonify(rooms)
    except Exception as e:
        print(f"Error getting rooms: {str(e)}") # Debug log
        return jsonify({'error': str(e)}), 500

@asset_routes.route('/api/inventory/export')
@login_required
def export_inventory():
    """Xuất báo cáo kiểm kê"""
    inventory_check_id = request.args.get('inventory_check_id')
    room_id = request.args.get('room_id')
    
    if not all([inventory_check_id, room_id]):
        return jsonify({'error': 'Thiếu thông tin cần thiết'}), 400
        
    try:
        # Gọi service để tạo báo cáo
        report = asset_service.generate_inventory_report(inventory_check_id, room_id)
        
        # Trả về file Excel
        return send_file(
            report,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'bao-cao-kiem-ke-{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@asset_routes.route('/api/inventory/active-checks')
@login_required
def get_active_inventory_checks():
    """API lấy danh sách đợt kiểm kê đang diễn ra (chỉ hiện hành)"""
    try:
        today = date.today().isoformat()
        response = SupabaseService().client.table('dotkiemke') \
            .select('*') \
            .lte('ngay_bat_dau', today) \
            .gte('ngay_ket_thuc', today) \
            .order('ngay_bat_dau', desc=True) \
            .execute()
            
        if not response.data:
            return jsonify([])
            
        # Format dữ liệu trả về
        inventory_checks = []
        for check in response.data:
            inventory_checks.append({
                'ma_dot_kiem_ke': check['ma_dot_kiem_ke'],
                'ten_dot': check['ten_dot'],
                'ngay_bat_dau': check['ngay_bat_dau'],
                'ngay_ket_thuc': check['ngay_ket_thuc']
            })
            
        return jsonify(inventory_checks)
    except Exception as e:
        print(f"Error getting inventory checks: {str(e)}")
        return jsonify({'error': str(e)}), 500