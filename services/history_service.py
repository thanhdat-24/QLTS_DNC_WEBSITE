from services.supabase_service import SupabaseService
from datetime import datetime

class HistoryService:
    """
    Dịch vụ quản lý lịch sử tài sản
    """
    def __init__(self):
        self.supabase = SupabaseService()
    
    def get_asset_history(self, asset_id):
        """
        Lấy lịch sử thay đổi của tài sản
    
        Args:
            asset_id: ID của tài sản
        
        Returns:
            Danh sách lịch sử thay đổi
        """
        # Lấy lịch sử từ bảng thông báo
        notifications = self.supabase.client.table('thongbao') \
            .select('*') \
            .eq('doi_tuong_tham_chieu', 'taisan') \
            .eq('ma_tham_chieu', asset_id) \
            .order('ngay_tao', desc=True) \
            .execute()
    
        # Lấy lịch sử thay đổi thông số của tài sản
        spec_changes = self._get_specification_history(asset_id)
    
        # Lấy lịch sử bàn giao tài sản
        handover_history = self._get_handover_history(asset_id)
    
        # Lấy lịch sử di chuyển tài sản
        movement_history = self._get_movement_history(asset_id)
    
        # Kết hợp tất cả lịch sử và sắp xếp theo thời gian giảm dần
        all_history = []
    
        # Xử lý thông báo
        for notification in notifications.data:
            # Định dạng ngày tạo
            created_at = self._format_datetime(notification.get('ngay_tao'))
        
            history_item = {
                'type': notification.get('loai_thongbao', 'info'),
                'message': notification.get('noi_dung', ''),
                'created_at': created_at,
                'created_at_raw': notification.get('ngay_tao', ''),  # Đảm bảo có giá trị mặc định
                'category': 'general',
                'link': notification.get('lien_ket', '')
            }
            all_history.append(history_item)
    
        # Thêm lịch sử thông số
        all_history.extend(spec_changes)
    
        # Thêm lịch sử bàn giao
        all_history.extend(handover_history)
    
        # Thêm lịch sử di chuyển
        all_history.extend(movement_history)
    
        # Sắp xếp theo thời gian giảm dần - sửa để xử lý giá trị None
        def sort_key(item):
            # Đảm bảo luôn có một giá trị để so sánh, nếu không có ngày thì dùng chuỗi rỗng
            raw_date = item.get('created_at_raw')
            return raw_date if raw_date is not None else ''
    
        all_history.sort(key=sort_key, reverse=True)
    
        return all_history
    
    def _get_specification_history(self, asset_id):
        """
        Lấy lịch sử thay đổi thông số của tài sản
        
        Args:
            asset_id: ID của tài sản
            
        Returns:
            Danh sách lịch sử thay đổi thông số
        """
        # Lấy lịch sử từ bảng thông báo có tham chiếu đến thông số
        spec_notifications = self.supabase.client.table('thongbao') \
            .select('*') \
            .eq('doi_tuong_tham_chieu', 'thongso_taisan') \
            .execute()
        
        # Lấy tất cả thông số của tài sản
        asset_specs = self.supabase.client.table('thongso_taisan') \
            .select('ma_thong_so_ts') \
            .eq('ma_tai_san', asset_id) \
            .execute()
        
        spec_ids = [spec['ma_thong_so_ts'] for spec in asset_specs.data]
        
        # Lọc chỉ lấy thông báo liên quan đến thông số của tài sản này
        spec_history = []
        for notification in spec_notifications.data:
            if notification.get('ma_tham_chieu') in spec_ids:
                # Định dạng ngày tạo
                created_at = self._format_datetime(notification.get('ngay_tao'))
                
                history_item = {
                    'type': notification.get('loai_thongbao', 'info'),
                    'message': notification.get('noi_dung', ''),
                    'created_at': created_at,
                    'created_at_raw': notification.get('ngay_tao'),
                    'category': 'specification',
                    'link': notification.get('lien_ket', '')
                }
                spec_history.append(history_item)
        
        return spec_history
    
    def _get_handover_history(self, asset_id):
        """
        Lấy lịch sử bàn giao tài sản
        
        Args:
            asset_id: ID của tài sản
            
        Returns:
            Danh sách lịch sử bàn giao
        """
        # Lấy danh sách chi tiết bàn giao có liên quan đến tài sản
        handovers = self.supabase.client.table('chitietbangiao') \
            .select('*, bangiaotaisan:ma_bang_giao_ts(ngay_bang_giao, noi_dung, ma_nv, phong:ma_phong(ten_phong))') \
            .eq('ma_tai_san', asset_id) \
            .execute()
        
        handover_history = []
        for handover in handovers.data:
            # Lấy thông tin từ bảng bàn giao
            handover_info = handover.get('bangiaotaisan', {})
            if not handover_info:
                continue
                
            # Ngày bàn giao
            handover_date = handover_info.get('ngay_bang_giao')
            created_at = self._format_datetime(handover_date)
            
            # Phòng
            room_name = handover_info.get('phong', {}).get('ten_phong', 'Chưa xác định')
            
            # Tạo thông điệp
            message = f"Tài sản được bàn giao đến phòng {room_name}"
            if handover_info.get('noi_dung'):
                message += f" - {handover_info.get('noi_dung')}"
                
            # Ghi chú từ chi tiết bàn giao
            note = handover.get('ghi_chu')
            if note:
                message += f" (Ghi chú: {note})"
            
            history_item = {
                'type': 'info',
                'message': message,
                'created_at': created_at,
                'created_at_raw': handover_date,
                'category': 'handover',
                'room': room_name,
                'link': f"/bangiao/{handover['ma_bang_giao_ts']}"
            }
            handover_history.append(history_item)
        
        return handover_history
    
    def _get_movement_history(self, asset_id):
        """
        Lấy lịch sử di chuyển tài sản
    
        Args:
            asset_id: ID của tài sản
        
        Returns:
            Danh sách lịch sử di chuyển
        """
        # Lấy lịch sử di chuyển từ bảng lichsudichuyentaisan
        # Chỉ lấy thông tin phòng cũ và phòng mới, bỏ tham chiếu đến ma_nv
        movements = self.supabase.client.table('lichsudichuyentaisan') \
            .select('*, phong_cu:ma_phong_cu(ten_phong), phong_moi:ma_phong_moi(ten_phong)') \
            .eq('ma_tai_san', asset_id) \
            .order('ngay_ban_giao', desc=True) \
            .execute()
    
        movement_history = []
        for movement in movements.data:
            # Lấy tên phòng cũ và mới
            old_room = movement.get('phong_cu', {}).get('ten_phong', 'Không xác định')
            new_room = movement.get('phong_moi', {}).get('ten_phong', 'Không xác định')
        
            # Định dạng ngày bàn giao
            movement_date = movement.get('ngay_bang_giao')
            created_at = self._format_datetime(movement_date)
        
            # Tạo thông điệp không có thông tin về nhân viên
            message = f"Tài sản được di chuyển từ {old_room} đến {new_room}"
        
            # Ghi chú 
            note = movement.get('ghi_chu')
            if note:
                message += f". Ghi chú: {note}"
        
            # Trạng thái di chuyển
            status = "Thành công" if movement.get('trang_thai') else "Chưa xác nhận"
        
            history_item = {
                'type': 'info',
                'message': message,
                'created_at': created_at,
                'created_at_raw': movement_date,
                'category': 'movement',
                'from_room': old_room,
                'to_room': new_room,
                'status': status
        }
            movement_history.append(history_item)
    
        return movement_history
    
    def _format_datetime(self, datetime_str):
        """
        Định dạng chuỗi datetime thành định dạng dễ đọc
        
        Args:
            datetime_str: Chuỗi datetime
            
        Returns:
            Chuỗi datetime đã định dạng
        """
        if not datetime_str:
            return ''
            
        try:
            dt_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt_obj.strftime('%d/%m/%Y %H:%M')
        except (ValueError, AttributeError, TypeError):
            return datetime_str
        
    def _get_asset_movement_history(self, asset_id):
        """
        Lấy lịch sử di chuyển tài sản từ bảng lichsudichuyentaisan
    
        Args:
            asset_id: ID của tài sản
        
        Returns:
            Danh sách lịch sử di chuyển
        """
        # Lấy lịch sử di chuyển tài sản
        movements = self.supabase.client.table('lichsudichuyentaisan') \
            .select('*, phong_cu:ma_phong_cu(ten_phong), phong_moi:ma_phong_moi(ten_phong), nhanvien:ma_nv(ho_ten)') \
            .eq('ma_tai_san', asset_id) \
            .order('ngay_bang_giao', desc=True) \
            .execute()
    
        movement_history = []
        for movement in movements.data:
            # Ngày bàn giao
            move_date = movement.get('ngay_bang_giao')
            created_at = self._format_datetime(move_date)
        
            # Phòng cũ và phòng mới
            old_room = movement.get('phong_cu', {}).get('ten_phong', 'Không xác định')
            new_room = movement.get('phong_moi', {}).get('ten_phong', 'Không xác định')
        
            # Nhân viên thực hiện
            staff_name = movement.get('nhanvien', {}).get('ho_ten', 'Không xác định')
        
            # Trạng thái
            status = "Hoàn thành" if movement.get('trang_thai') else "Đang xử lý"
        
            # Tạo thông điệp
            message = f"Di chuyển tài sản từ {old_room} đến {new_room} bởi {staff_name}"
        
            # Ghi chú
            note = movement.get('ghi_chu')
            if note:
                message += f" (Ghi chú: {note})"
        
            history_item = {
                'type': 'info',
                'message': message,
                'created_at': created_at,
                'created_at_raw': move_date,
                'category': 'movement',
                'old_room': old_room,
                'new_room': new_room,
                'staff': staff_name,
                'status': status
            }
            movement_history.append(history_item)
    
        return movement_history